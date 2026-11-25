"""採用した画像（source/）を受け渡しの形に書き出す。GPU は要らない。"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
from pathlib import Path

from PIL import Image

from artgen.config import ConfigError, Cutout, load_character, load_template
from artgen.cutout import output_name, output_size, prepared_mask, render
from artgen.matte import load_matte_with_sha
from artgen.pnginfo import MissingParamsError, read_params


class ExportError(Exception):
    """書き出せない入力（名前・形・条件の不足）。"""


def check_dir(root: Path, char_id: str) -> Path:
    """確認図（透明にした画素を赤で塗った絵）の置き場。リポジトリに入れない。"""
    return Path(root) / "local" / "check" / char_id


def cutout_record(
    cutout: Cutout,
    source_dir: Path,
    names: list[str],
    matte_shas: dict[str, str] | None = None,
    source_shas: dict[str, str] | None = None,
) -> dict:
    """params.json の cutouts に書く、テンプレート 1 つぶんの記録。使った設定と、切り出した元の絵の SHA-256。
    承認用ページ（cutout_review）が、書き出しが今の設定・今の元の絵・今のマスクのものかを照合するのに使う。
    matte_shas は書き出しが描画に使ったマスクの SHA-256（読み込んだ bytes から求めたもの）。
    無ければ今の matte/ のファイルから求める（無いファイルは None）。
    source_shas は書き出しが描画に使った元の絵の bytes の SHA-256。無ければ今の source/ のファイルから求める。"""
    record = {
        "background": cutout.background,
        # min_rg は書いたときだけ記録する
        "clear_colors": [
            {"min": c.min, "max_rg": c.max_rg, "max_gb": c.max_gb, **({"min_rg": c.min_rg} if c.min_rg is not None else {})}
            for c in cutout.clear_colors
        ],
        "erase": [[list(p) for p in poly] for poly in cutout.erase],
        "outputs": [
            {"suffix": o.suffix, "box": list(o.box) if o.box is not None else None, "width": o.width}
            for o in cutout.outputs
        ],
        "source_sha256": {
            n: (source_shas[n] if source_shas is not None else hashlib.sha256((source_dir / n).read_bytes()).hexdigest())
            for n in sorted(names)
        },
    }
    if cutout.background == "matte":
        matte_dir = source_dir.parent / "matte"
        if matte_shas is not None:
            record["matte_sha256"] = {n: matte_shas.get(n) for n in sorted(names)}
        else:
            record["matte_sha256"] = {
                n: hashlib.sha256((matte_dir / n).read_bytes()).hexdigest() if (matte_dir / n).is_file() else None
                for n in sorted(names)
            }
    return record


def _accepted_names(expressions: list[str]) -> list[str]:
    return ["face.png", *(f"face_{e}.png" for e in expressions), "fullbody.png"]


def _check_matches_name(src: Path, rel_source: str, params: dict, template_name: str, character) -> None:
    """ファイル名から決まる型・表情と、画像の中身・条件が合っているか。取り違えと縮小を止める。"""
    where = f"{rel_source}/{src.name}"
    stem = src.stem
    if stem == "fullbody":
        want_template, want_expression = "fullbody", None
    elif stem == "face":
        want_template, want_expression = "face", character.default_expression
    else:
        want_template, want_expression = "face", stem.removeprefix("face_")
    if template_name != want_template:
        raise ExportError(f"{where}: 条件の template が {template_name!r}。この名前には {want_template!r} の絵が要る")
    if want_expression is not None and params.get("expression", want_expression) != want_expression:
        raise ExportError(
            f"{where}: 条件の expression が {params['expression']!r}。この名前には {want_expression!r} の絵が要る"
        )
    if params.get("character", character.id) != character.id:
        raise ExportError(f"{where}: 条件の character が {params['character']!r}（{character.id!r} の絵でない）")
    w, h = params.get("width"), params.get("height")
    if isinstance(w, int) and isinstance(h, int):
        with Image.open(src) as im:
            if im.size != (w, h):
                raise ExportError(
                    f"{where}: 画像が {im.width}x{im.height} で、条件の {w}x{h} と違う。"
                    "添付で縮められた可能性がある"
                )


def export_character(root: Path, char_id: str) -> list[Path]:
    """`characters/<id>/source/*.png` を `characters/<id>/` に書き出し、params.json を作る。

    すべての入力（設定・元の絵・マスク）を検査してから書き始めるので、途中で止まっても何も書かれない。
    テンプレートに `cutouts` があれば、その出力ごとに範囲を切り抜いて背景を透明にした RGBA を書く。
    """
    root = Path(root)
    if not char_id or Path(char_id).name != char_id or char_id in (".", ".."):
        raise ExportError(f"キャラクターの ID が不正: {char_id!r}")
    character = load_character(root, char_id)
    char_dir = root / "characters" / char_id
    source_dir = char_dir / "source"
    rel_source = f"characters/{char_id}/source"

    if not source_dir.is_dir():
        raise ExportError(f"{rel_source}: フォルダが無い")
    # 隠しファイル（.DS_Store など）は無視する。それ以外は名前を検査する（face.PNG・jpg も止める）
    sources = sorted(p for p in source_dir.iterdir() if p.is_file() and not p.name.startswith("."))
    if not sources:
        raise ExportError(f"{rel_source}: PNG が無い")

    accepted = _accepted_names(list(character.expressions))
    # (元の絵, 出力先, export_size, cutout)。cutout があるときは出力先と export_size を使わない
    plans: list[tuple[Path, Path, int | None, Cutout | None]] = []
    all_params: dict[str, dict] = {}
    source_data: dict[str, bytes] = {}
    source_shas: dict[str, str] = {}
    for src in sources:
        if src.name not in accepted:
            raise ExportError(
                f"{rel_source}/{src.name}: 受け付けない名前（受け付ける名前: {', '.join(accepted)}）"
            )
        params = read_params(src)  # 無ければ MissingParamsError のまま上げる
        template_name = params.get("template")
        if not isinstance(template_name, str):
            raise ExportError(f"{rel_source}/{src.name}: 条件に template が無い")
        template = load_template(root, template_name)
        _check_matches_name(src, rel_source, params, template_name, character)

        cutout = character.cutouts.get(template_name)
        # 元の絵は 1 回だけ読み、検査・マスクとの照合・描画・記録に同じ bytes を使う（途中で差し替わっても食い違わない）
        data = src.read_bytes()
        source_data[src.name] = data
        source_shas[src.name] = hashlib.sha256(data).hexdigest()
        with Image.open(io.BytesIO(data)) as im:
            if cutout is not None:
                for i, output in enumerate(cutout.outputs):
                    box = output.box
                    size = output_size(box or (0, 0, im.width, im.height), output.width)
                    if min(size) < 1:
                        raise ConfigError(
                            f"characters/{char_id}/character.yaml: cutouts.{template_name}.outputs[{i}].width: "
                            f"元の絵 {src.name}（{im.width}x{im.height}）では出力の大きさが {size[0]}x{size[1]} になる"
                        )
                    if box is not None and (box[2] > im.width or box[3] > im.height):
                        raise ConfigError(
                            f"characters/{char_id}/character.yaml: cutouts.{template_name}.outputs[{i}].box: "
                            f"範囲 {list(box)} が元の絵 {src.name}（{im.width}x{im.height}）の外にはみ出す"
                        )
            elif template.export_size is not None and im.width != im.height:
                raise ExportError(
                    f"{rel_source}/{src.name}: 正方形でない（{im.width}x{im.height}）。"
                    "顔は正方形で生成する"
                )
        plans.append((src, char_dir / src.name, template.export_size, cutout))
        all_params[src.name] = params

    checks = check_dir(root, char_id)
    # 書き出すファイルと確認図。これに無い古い出力は、params.json と食い違うので消す
    owners: dict[Path, str] = {}

    def claim(path: Path, owner: str) -> None:
        # 表情名が `normal` と `normal-small` のように、別の入力の出力が同じ名前になるときは、書く前に止める
        if owners.setdefault(path, owner) != owner:
            raise ExportError(f"{path.name}: {owners[path]} と {owner} の出力が同じ名前になる（表情名を変える）")

    for src, dest, _, cutout in plans:
        if cutout is None:
            claim(dest, src.name)
            continue
        for output in cutout.outputs:
            name = output_name(src.name, output.suffix)
            claim(char_dir / name, src.name)
            claim(checks / name, src.name)

    # マスクも、今の出力を消したり書き換えたりする前に全部読んで検査する
    # （表情のマスクだけが古いときに、顔だけを書き換えてから止まると、出力と params.json が食い違う）
    masks: dict[str, Image.Image] = {}
    mask_shas: dict[str, str] = {}  # 記録には、描画に使うこのマスクの SHA-256 を書く（後で更新されても食い違わない）
    for src, _, _, cutout in plans:
        if cutout is not None and cutout.background == "matte":
            loaded, mask_shas[src.name] = load_matte_with_sha(
                root, char_id, src.name, source_sha=source_shas[src.name]
            )
            masks[src.name] = prepared_mask(loaded, cutout.erase)

    # 書く絵は、何かを消す前に全部作る
    rendered: list[tuple[Path, Image.Image, Path | None, Image.Image | None]] = []
    for src, dest, size, cutout in plans:
        if cutout is None:
            continue
        with Image.open(io.BytesIO(source_data[src.name])) as im:
            for output in cutout.outputs:
                name = output_name(src.name, output.suffix)
                image, check = render(im, output, cutout.background, cutout.clear_colors, masks.get(src.name))
                rendered.append((char_dir / name, image, checks / name, check))

    # 消す: 今回の出力に無い、受け付ける名前（と、その名前に `-` 付きの名前）と、確認図
    wanted = set(owners)
    # 今の設定で受け付ける名前に加え、前回の書き出しの記録にあった名前（設定から外した表情など）も消す対象にする
    managed = set(accepted)
    previous_params = char_dir / "params.json"
    if previous_params.is_file():
        try:
            previous = json.loads(previous_params.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = None
        if isinstance(previous, dict):  # 壊れた記録（辞書でない・読めない）は無視し、書き出しの最後で作り直す
            managed |= {k for k in previous if isinstance(k, str) and k.endswith(".png")}
    stems = [name.removesuffix(".png") for name in managed]
    if char_dir.is_dir():
        for old in char_dir.glob("*.png"):
            stem = old.stem
            if old not in wanted and (old.name in managed or any(stem.startswith(f"{s}-") for s in stems)):
                old.unlink()
    if checks.is_dir():
        for old in checks.glob("*.png"):
            if old not in wanted:
                old.unlink()

    written: list[Path] = []
    for src, dest, size, cutout in plans:
        if cutout is not None:
            continue
        if size is None:
            shutil.copyfile(src, dest)
        else:
            with Image.open(src) as im:
                im.convert("RGB").resize((size, size), Image.Resampling.LANCZOS).save(dest, format="PNG")
        written.append(dest)
    for out_path, image, check_path, check in rendered:
        checks.mkdir(parents=True, exist_ok=True)
        image.save(out_path, format="PNG")
        check.save(check_path, format="PNG")
        written.append(out_path)

    records: dict[str, dict] = {}
    for template_name, cutout in character.cutouts.items():
        names = [src.name for src, _, _, c in plans if c is cutout]
        if names:
            shas = mask_shas if cutout.background == "matte" else None
            records[template_name] = cutout_record(cutout, source_dir, names, shas, source_shas)
    if records:
        all_params["cutouts"] = records
    params_path = char_dir / "params.json"
    params_path.write_text(
        json.dumps(all_params, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    written.append(params_path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m artgen.export", description="採用した画像を書き出す")
    parser.add_argument("char_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        paths = export_character(args.root, args.char_id)
    except (ExportError, MissingParamsError, ConfigError) as e:
        print(f"書き出せない: {e}")
        return 1
    for p in paths:
        print(f"書き出した: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
