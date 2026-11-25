"""元の絵の範囲の切り抜きと、背景を透明にする描画。

背景の消し方は 3 つ。
- matte: `characters/<id>/matte/` のマスクをアルファにする（形で判定。背景の飾りや髪に囲まれた白も消える）
- colors: 切り出した範囲の四辺から続く「白」と `clear_colors` に当たる画素を透明にする。範囲の内側にあって
  外につながらない白（白目・服の白など）は残る。範囲の辺で服が切れていると服の白も透明になる
- none: 透明にしない

どれも、透明にした画素を赤で塗った確認図（縮める前）を一緒に返す。確認図は必ず目で見る。
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from PIL import Image, ImageDraw

from artgen.config import ClearColor, CutoutOutput
from artgen.matte import harden

WHITE_MIN = 240
_RED = (255, 0, 0)


def output_name(source_name: str, suffix: str) -> str:
    """元の絵の名前に suffix を付けた出力の名前（face_hurt.png + -small → face_hurt-small.png）。"""
    stem, dot, ext = source_name.rpartition(".")
    return f"{stem}{suffix}{dot}{ext}"


def output_size(box: tuple[int, int, int, int], width: int | None) -> tuple[int, int]:
    """出力の大きさ。width が None なら範囲の大きさ、あれば縦横の比を保った高さ（四捨五入）。"""
    x0, y0, x1, y1 = box
    if width is None:
        return (x1 - x0, y1 - y0)
    return (width, round(width * (y1 - y0) / (x1 - x0)))


def prepared_mask(mask: Image.Image, erase) -> Image.Image:
    """マスクを harden し、erase の多角形の中を透明（0）にする。"""
    out = harden(mask)
    draw = ImageDraw.Draw(out)
    for polygon in erase:
        draw.polygon(list(polygon), fill=0)
    return out


def _clearable(pixel: tuple[int, int, int], colors: Sequence[ClearColor]) -> bool:
    r, g, b = pixel
    lo = min(pixel)
    if lo >= WHITE_MIN:
        return True
    return any(
        lo >= c.min and r - g <= c.max_rg and g - b <= c.max_gb and (c.min_rg is None or r - g >= c.min_rg)
        for c in colors
    )


def clear_background(
    image: Image.Image, colors: Sequence[ClearColor]
) -> tuple[Image.Image, Image.Image]:
    """RGB の絵の外につながる背景を透明にする。（透明化した RGBA、確認図の RGB）を返す。"""
    rgb = image.convert("RGB")
    w, h = rgb.size
    src = rgb.load()
    cleared = bytearray(w * h)
    queue: deque[tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        if not cleared[y * w + x] and _clearable(src[x, y], colors):
            cleared[y * w + x] = 1
            queue.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)
    while queue:
        x, y = queue.popleft()
        if x > 0:
            push(x - 1, y)
        if x < w - 1:
            push(x + 1, y)
        if y > 0:
            push(x, y - 1)
        if y < h - 1:
            push(x, y + 1)

    out = rgb.convert("RGBA")
    check = rgb.copy()
    dst, chk = out.load(), check.load()
    for y in range(h):
        for x in range(w):
            if cleared[y * w + x]:
                dst[x, y] = (*src[x, y], 0)
                chk[x, y] = _RED
    return out, check


def render(
    source: Image.Image,
    output: CutoutOutput,
    background: str,
    clear_colors: Sequence[ClearColor],
    mask: Image.Image | None,
) -> tuple[Image.Image, Image.Image]:
    """output の範囲を切り出して背景を消し、縮める。（縮めた RGBA、縮める前の確認図 RGB）を返す。
    mask は background == "matte" のときの、prepared_mask を済ませた元の絵と同じ大きさのマスク。"""
    rgb = source.convert("RGB")
    box = output.box or (0, 0, rgb.width, rgb.height)
    cropped = rgb.crop(box)
    if background == "matte":
        if mask is None:
            raise ValueError("background: matte にはマスクが要る")
        alpha = mask.convert("L").crop(box)
        full = cropped.convert("RGBA")
        full.putalpha(alpha)
        check = cropped.copy()
        check.paste(Image.new("RGB", check.size, _RED), mask=alpha.point(lambda v: 255 if v < 128 else 0))
    elif background == "colors":
        full, check = clear_background(cropped, clear_colors)
    else:
        full, check = cropped.convert("RGBA"), cropped.copy()
    size = output_size(box, output.width)
    if size != full.size:
        # アルファを掛けた形で縮め、透明の縁が黒ずむのを防ぐ
        full = full.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    return full, check
