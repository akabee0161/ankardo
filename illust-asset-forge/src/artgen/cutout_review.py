"""切り出しの範囲と背景消しを依頼者に承認してもらうための HTML ページを作る。

`python -m artgen.cutout_review <id>` が `local/check/<id>/review.html` を作る。
`python -m artgen.cutout_review <id> <id> ... [--out PATH]` は何人分かを 1 枚のページ
（既定は `local/check/reviews/<日時>.html`）にまとめる。全員を先に検査し、1 人でも書き出しが古ければ作らない。
画像は data URI で埋め込むので、1 ファイルのまま Artifact で公開できる。
何人分かのページでは、元の絵と確認図を JPEG に縮める。書き出した絵は PNG のまま。
表情（`face_<表情>.png`）は `--variants` を付けたときだけ並べる（検査は付けなくても全部の絵で行う）。
先に `python -m artgen.export <id>` で書き出しておく。
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

from artgen.config import Character, ConfigError, Cutout, CutoutOutput, load_character, load_preview_background
from artgen.cutout import output_name
from artgen.export import ExportError, check_dir, cutout_record
from artgen.pnginfo import MissingParamsError, read_params

PREVIEW_SOURCE_PX = 512
MANY_CHECK_PX = 320  # 何人分かのページの確認図の長辺
MANY_JPEG_QUALITY = 85
_FRAME_COLORS = ((255, 0, 0), (0, 112, 255), (0, 160, 0), (200, 0, 200))
_STALE = (
    "characters/{char}/params.json: 書き出しの記録が無いか、character.yaml の cutouts・元の絵・マスクと違う。"
    "先に python -m artgen.export {char} を実行する"
)


@dataclass
class _Output:
    name: str
    spec: CutoutOutput
    check: Image.Image
    exported: Image.Image


@dataclass
class _Item:
    source_name: str
    source: Image.Image
    outputs: list[_Output]


@dataclass
class _Template:
    name: str
    cutout: Cutout
    items: list[_Item]


@dataclass
class _Parts:
    char_id: str
    character: Character
    templates: list[_Template]
    preview_bg: str | None


def _png_uri(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _jpeg_uri(image: Image.Image, longest: int | None = None) -> str:
    im = image.convert("RGBA")
    if longest is not None:
        im.thumbnail((longest, longest), Image.Resampling.LANCZOS)
    flat = Image.new("RGB", im.size, (255, 255, 255))  # JPEG は透明を持てない（確認図は透明部分が無い）
    flat.paste(im, mask=im.getchannel("A"))
    buf = io.BytesIO()
    flat.save(buf, format="JPEG", quality=MANY_JPEG_QUALITY)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _load(path: Path, what: str, char_id: str) -> Image.Image:
    if not path.is_file():
        raise ExportError(f"{path}: {what}が無い。先に python -m artgen.export {char_id} を実行する")
    with Image.open(path) as im:
        im.load()
        return im.copy()


def _sources_by_template(source_dir: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    if not source_dir.is_dir():
        return found
    for src in sorted(source_dir.iterdir()):
        if not src.is_file() or src.name.startswith("."):
            continue
        try:
            template = read_params(src).get("template")
        except MissingParamsError as e:
            raise ExportError(f"{src}: 条件が無い絵が source/ にある: {e}") from e
        if isinstance(template, str):
            found.setdefault(template, []).append(src.name)
    return found


def _collect(root: Path, char_id: str, variants: bool) -> _Parts:
    """書き出しが今の設定・元の絵・マスクと合うかを検査し、ページに載せる画像を読む。"""
    character = load_character(root, char_id)
    if not character.cutouts:
        raise ExportError(f"characters/{char_id}/character.yaml: cutouts が無い（承認するものが無い）")
    char_dir = root / "characters" / char_id
    source_dir = char_dir / "source"
    checks = check_dir(root, char_id)

    # 範囲や erase を直した・元の絵を入れ替えた・マスクを作り直したのに export を忘れると、
    # 古い画像に新しい枠を描いたページになり、承認が意味を失う。書き出しの記録（params.json の cutouts）が
    # 今の設定・元の絵・マスクと合わないときは作らない。表情も含めた全部で検査する
    names_by_template = _sources_by_template(source_dir)
    expected = {
        template: cutout_record(cutout, source_dir, names_by_template[template])
        for template, cutout in character.cutouts.items()
        if names_by_template.get(template)
    }
    params_path = char_dir / "params.json"
    recorded = None
    if params_path.is_file():
        try:
            recorded = json.loads(params_path.read_text(encoding="utf-8")).get("cutouts")
        except (OSError, json.JSONDecodeError, AttributeError) as e:
            raise ExportError(f"characters/{char_id}/params.json: 読めない: {e}") from e
    if not expected or recorded != expected:
        raise ExportError(_STALE.format(char=char_id))

    templates = []
    for template, cutout in character.cutouts.items():
        names = names_by_template.get(template, [])
        shown = names if variants else [n for n in names if n == f"{template}.png"]
        items = []
        for name in shown:
            outputs = []
            for spec in cutout.outputs:
                out_name = output_name(name, spec.suffix)
                outputs.append(
                    _Output(
                        out_name,
                        spec,
                        _load(checks / out_name, "確認図（書き出し）", char_id),
                        _load(char_dir / out_name, "書き出した絵", char_id),
                    )
                )
            items.append(_Item(name, _load(source_dir / name, "元の絵", char_id).convert("RGB"), outputs))
        if items:
            templates.append(_Template(template, cutout, items))
    return _Parts(char_id, character, templates, load_preview_background(root))


def _item_html(item: _Item, preview_bg: str | None, many: bool, tag: str) -> str:
    scale = PREVIEW_SOURCE_PX / max(item.source.size)
    plain = item.source.resize(
        (round(item.source.width * scale), round(item.source.height * scale)), Image.Resampling.LANCZOS
    )
    framed = plain.copy()
    draw = ImageDraw.Draw(framed)
    legend = []
    for i, out in enumerate(item.outputs):
        if out.spec.box is None:
            continue
        color = _FRAME_COLORS[i % len(_FRAME_COLORS)]
        draw.rectangle([round(v * scale) for v in out.spec.box], outline=color, width=3)
        legend.append(
            f'<span style="color:rgb{color}">■</span> {html.escape(out.name)} 範囲 {list(out.spec.box)}'
        )

    def source_uri(im: Image.Image) -> str:
        return _jpeg_uri(im) if many else _png_uri(im)

    def check_uri(im: Image.Image) -> str:
        return _jpeg_uri(im, MANY_CHECK_PX) if many else _png_uri(im)

    figures = [
        ("元の絵（範囲の枠つき）", source_uri(framed)),
        ("元の絵（枠なし）", source_uri(plain)),
    ]
    figure_html = "".join(
        f'<figure><img alt="{label}" src="{uri}" style="max-width:100%"><figcaption>{label}</figcaption></figure>'
        for label, uri in figures
    ) + "".join(
        f'<figure><img alt="確認図 {html.escape(o.name)}" src="{check_uri(o.check)}" style="max-width:100%">'
        f"<figcaption>確認図 {html.escape(o.name)}（赤＝透明にした画素）</figcaption></figure>"
        for o in item.outputs
    )

    def exported_figure(o: _Output, preview: bool) -> str:
        w, h = o.exported.size
        img = f'<img src="{_png_uri(o.exported)}" width="{w}" height="{h}" alt="{html.escape(o.name)}">'
        caption = f"{html.escape(o.name)}（{w}x{h}）"
        if preview:
            return f'<figure><div class="preview" style="background:{preview_bg}">{img}</div><figcaption>{caption}</figcaption></figure>'
        return f"<figure>{img}<figcaption>{caption}</figcaption></figure>"

    on_checker = "".join(exported_figure(o, False) for o in item.outputs)
    on_preview = ""
    if preview_bg is not None:
        on_preview = (
            f'<{tag}>表示用の背景の上（{html.escape(preview_bg)}）</{tag}><div class="row">'
            + "".join(exported_figure(o, True) for o in item.outputs)
            + "</div>"
        )
    return (
        f"<{tag}>{html.escape(item.source_name)}</{tag}>\n"
        f"<p>{'／'.join(legend) if legend else '範囲: 絵の全体'}</p>\n"
        f'<div class="row">{figure_html}</div>\n'
        f"<{tag}>書き出した絵（書き出した大きさ、市松模様の上）</{tag}>"
        f'<div class="row checker">{on_checker}</div>\n{on_preview}'
    )


def _body(p: _Parts, many: bool) -> str:
    tag = "h3" if many else "h2"
    sub = "h4" if many else "h3"
    block = "div" if many else "section"  # 何人分かのページでは、<section> は 1 人に 1 つ
    parts = []
    for t in p.templates:
        items = "".join(_item_html(item, p.preview_bg, many, sub) for item in t.items)
        parts.append(
            f'<{block} class="block"><{tag}>{html.escape(t.name)}（背景: {html.escape(t.cutout.background)}）</{tag}>{items}</{block}>\n'
        )
    return "".join(parts)


def _page(title: str, content: str) -> str:
    # Artifact として公開できるよう、<html>・<head>・<body> を書かない形にする（公開時に枠が付く）
    return f"""<title>{html.escape(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root {{ --bg: #f6f7f9; --fg: #1d232b; --muted: #5b6673; --line: #d5dae1;
  --check-a: #dfe3e8; --check-b: #ffffff; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #12171d; --fg: #e7ecf2; --muted: #9aa6b4; --line: #2c3541;
  --check-a: #2a323c; --check-b: #1b2128; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg: #12171d; --fg: #e7ecf2; --muted: #9aa6b4; --line: #2c3541;
  --check-a: #2a323c; --check-b: #1b2128; color-scheme: dark; }}
body {{ background: var(--bg); color: var(--fg); font-family: Inter, "Hiragino Sans", "Noto Sans JP", sans-serif;
  padding-block: 20px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
h1 {{ font-size: 20px; margin: 0 0 4px; text-wrap: balance; }}
h2 {{ font-size: 15px; margin: 0 0 8px; }}
section.char > h2 {{ font-size: 18px; padding-bottom: 4px; border-bottom: 1px solid var(--line); }}
h3 {{ font-size: 14px; margin: 12px 0 8px; }}
h4 {{ font-size: 13px; margin: 12px 0 8px; }}
p {{ color: var(--muted); margin: 0 0 12px; }}
.block, section.char {{ margin-bottom: 28px; }}
.row {{ display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-start; }}
figure {{ margin: 0; max-width: 100%; min-width: 0; }}
figure img {{ display: block; max-width: 100%; height: auto; border: 1px solid var(--line); }}
.checker figure img {{ background: repeating-conic-gradient(var(--check-a) 0 25%, var(--check-b) 0 50%) 0 0 / 16px 16px; }}
.preview {{ display: inline-block; padding: 16px; }}
.preview img {{ border: 0; }}
figcaption {{ font-size: 13px; color: var(--muted); margin-top: 4px; }}
</style>
{content}"""


def build_review(root: Path, char_id: str, variants: bool = False) -> Path:
    root = Path(root)
    out = root / "local" / "check" / char_id / "review.html"
    try:
        p = _collect(root, char_id, variants)
    except (ExportError, ConfigError):
        out.unlink(missing_ok=True)  # 前の範囲のページが残ると、古い範囲で承認してしまう
        raise
    heading = html.escape(f"{p.character.name}（{char_id}）切り出し")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_page(f"{p.character.name} 切り出し", f"<h1>{heading}</h1>\n{_body(p, many=False)}"), encoding="utf-8")
    return out


def build_reviews(root: Path, char_ids: list[str], out: Path | None = None, variants: bool = False) -> Path:
    """何人分かの承認用のページを 1 枚にまとめる。全員の検査を先に済ませ、1 人でも通らなければ何も書かない。"""
    root = Path(root)
    parts = []
    for char_id in char_ids:
        try:
            parts.append(_collect(root, char_id, variants))
        except (ExportError, ConfigError) as e:
            if out is not None:
                Path(out).unlink(missing_ok=True)  # 前の範囲のページが残ると、古い範囲で承認してしまう
            message = str(e) if char_id in str(e) else f"{char_id}: {e}"
            raise type(e)(message) from e
    sections = "".join(
        f'<section class="char"><h2>{html.escape(f"{p.character.name}（{p.char_id}）")}</h2>\n{_body(p, many=True)}</section>\n'
        for p in parts
    )
    if out is None:
        out = root / "local" / "check" / "reviews" / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    title = f"切り出し {len(parts)} 人"
    out.write_text(_page(title, f"<h1>{html.escape(title)}</h1>\n{sections}"), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m artgen.cutout_review", description="切り出しの承認用ページを作る")
    parser.add_argument("char_ids", nargs="+", metavar="char_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=None, help="何人分かのページの置き場（既定は local/check/reviews/<日時>.html）")
    parser.add_argument("--variants", action="store_true", help="表情の差分（face_<表情>.png）も並べる")
    args = parser.parse_args(argv)
    try:
        if len(args.char_ids) == 1 and args.out is None:
            path = build_review(args.root, args.char_ids[0], args.variants)
        else:
            path = build_reviews(args.root, args.char_ids, args.out, args.variants)
    except (ExportError, ConfigError) as e:
        print(f"作れない: {e}")
        return 1
    print(f"作った: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
