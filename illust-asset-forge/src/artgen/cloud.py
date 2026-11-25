"""Claude がこのサーバーで叩く CLI。Modal で候補を作り、`local/` から採用・取り込みする。

    python -m artgen.cloud generate --jobs FILE
    python -m artgen.cloud page ROUND_JSON
    python -m artgen.cloud merge ROUND_JSON ROUND_JSON [...]
    python -m artgen.cloud matte CHAR [CHAR ...]
    python -m artgen.cloud adopt ROUND_JSON NUMBER [--flip]
    python -m artgen.cloud install CHAR [CHAR ...]

forge のフォルダ（このリポジトリの根。コピー先ではコピーを置いたフォルダ）で実行する（`--root` で変えられる）。
Modal は `generate` の中でだけ import する（ほかのコマンドとテストは Modal が無くても動く）。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from artgen.config import ConfigError, load_character
from artgen.export import ExportError, _accepted_names
from artgen.intake import install_selection, print_reports
from artgen.jobs import collect_faces, load_jobs
from artgen.local import local_commit, local_dirs, save_outputs
from artgen.matte import MODEL_SHA256, ensure_candidate_mattes, save_mattes
from artgen.pnginfo import MissingParamsError, read_params
from artgen.review_page import build_page
from artgen.rounds import new_round, read_round, unused_run_id
from artgen.selection import SelectionStore, _check_name_part, file_sha256

_STOPS = (ConfigError, ExportError, MissingParamsError, OSError, RuntimeError)


def _page_path(round_json: Path) -> Path:
    return round_json.with_suffix(".html")


def _build(round_json: Path, root: Path, matte: bool) -> Path:
    """候補のページを作る。matte なら、まだマスクの無い候補の背景を先に Modal で消す
    （選んだ後に背景が消えないと分かると選び直しになるため、選ぶ前に見せる）。"""
    round_ = read_round(round_json)
    if matte:
        from artgen import modal_app  # Modal はここでだけ import する

        sent = ensure_candidate_mattes([c.path for c in round_.candidates], modal_app.run_matte)
        print(f"背景を消した: {sent} 枚（済んでいた {len(round_.candidates) - sent} 枚は送っていない）")
    return build_page(round_, _page_path(round_json), root=root)


def _build_or_explain(round_json: Path, root: Path, matte: bool) -> Path:
    """_build と同じ。背景消しが落ちたら、作った絵と記録は残っていて page でやり直せると言って止まる。"""
    try:
        return _build(round_json, root, matte)
    except Exception as e:  # Modal の例外（modal.exception.*）は RuntimeError の子でない
        raise RuntimeError(
            f"{e}（絵と回りの記録は残っている。python -m artgen.cloud page {round_json} でやり直せる）"
        ) from e


def cmd_generate(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    dirs = local_dirs(root)
    jobs = load_jobs(args.jobs, root)  # Modal を起動する前に、ジョブの誤りを止める
    faces = collect_faces(dirs.selected, jobs)
    from artgen import modal_app  # Modal はここでだけ import する

    if root != Path(modal_app.FORGE_DIR).resolve():
        # Modal に送る設定は、このパッケージのフォルダ（FORGE_DIR）から取る。別のフォルダの設定・commit と
        # 食い違う絵ができるので、generate では --root で別のフォルダを指せない
        raise ConfigError(
            f"--root: generate は、Modal に送るフォルダ（{modal_app.FORGE_DIR}）でしか使えない。"
            f"そのフォルダの .venv で実行する（指したのは {root}）"
        )
    outputs = modal_app.run(jobs, local_commit(root), faces)
    paths = save_outputs(dirs.runs, outputs)
    run_id = unused_run_id(dirs.rounds, datetime.now().strftime("%Y%m%d_%H%M%S"))
    round_json = new_round(dirs.rounds, run_id, paths)
    del outputs  # 絵の bytes（100MB を超える）を、背景消しで送る前に手放す
    print(f"{len(paths)} 枚できた")
    print(f"回りの記録: {round_json}")  # 背景消しが落ちても、記録の場所が分かるように先に出す
    page = _build_or_explain(round_json, root, not args.no_matte)
    print(f"候補のページ: {page}")


def cmd_page(args: argparse.Namespace) -> None:
    page = _build(args.round_json, args.root.resolve(), not args.no_matte)
    print(f"候補のページ: {page}")


def cmd_merge(args: argparse.Namespace) -> None:
    """何回かに分けて作った回りを 1 つの記録とページにまとめる。番号は通しで振り直し、元の記録は変えない。"""
    if len(args.rounds) < 2:
        raise ConfigError("merge: 回りの記録を 2 つ以上渡す")
    root = args.root.resolve()
    dirs = local_dirs(root)
    paths = [c.path for r in args.rounds for c in sorted(read_round(r).candidates, key=lambda c: c.number)]
    run_id = unused_run_id(dirs.rounds, "merged_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    round_json = new_round(dirs.rounds, run_id, paths)
    print(f"{len(paths)} 枚をまとめた")
    print(f"回りの記録: {round_json}")
    page = _build_or_explain(round_json, root, not args.no_matte)
    print(f"候補のページ: {page}")


def cmd_matte(args: argparse.Namespace) -> None:
    """cutouts で background: matte のテンプレートの元の絵（source/）を Modal に送り、
    背景のマスクを characters/<id>/matte/ に置く。"""
    root = args.root.resolve()
    images: dict[str, bytes] = {}
    for char in args.chars:
        _check_name_part(char, "character")
        cutouts = load_character(root, char).cutouts
        source_dir = root / "characters" / char / "source"
        found = 0
        for f in sorted(source_dir.glob("*.png")) if source_dir.is_dir() else []:
            if f.name.startswith("."):
                continue
            cutout = cutouts.get(read_params(f).get("template"))
            if cutout is not None and cutout.background == "matte":
                images[f"{char}/{f.name}"] = f.read_bytes()
                found += 1
        if not found:
            raise ConfigError(
                f"characters/{char}: マスクで背景を消す元の絵が無い（cutouts の background: matte と source/）"
            )
    from artgen import modal_app  # Modal はここでだけ import する

    model_sha, masks = modal_app.run_matte(images)
    if model_sha == MODEL_SHA256 and set(masks) != set(images):
        raise ExportError(f"Modal が返したマスクが足りない（{len(masks)} 枚。{len(images)} 枚のはず）。何も置いていない")
    for char in args.chars:
        mine = {k.split("/", 1)[1]: v for k, v in masks.items() if k.split("/", 1)[0] == char}
        sent = {name: images[f"{char}/{name}"] for name in mine}
        save_mattes(root, char, mine, model_sha, sent=sent)
        print(f"マスクを作った: {char}（{len(mine)} 枚）")


def cmd_adopt(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    dirs = local_dirs(root)
    round_ = read_round(args.round_json)
    found = [c for c in round_.candidates if c.number == args.number]
    if not found:
        numbers = [c.number for c in round_.candidates]
        raise ConfigError(f"番号 {args.number} の候補が無い（{min(numbers)}〜{max(numbers)}）")
    candidate = found[0]
    dest = SelectionStore(dirs.selected, dirs.packs).adopt(candidate.path, flip=args.flip)
    print(f"採用した: {dest}")


def _installed_record(dirs, char: str) -> Path:
    return dirs.installed / f"{char}.json"


def _read_installed(path: Path) -> dict[str, str]:
    """前回の取り込みで `local/selected/<id>/` から入れた絵の名前と SHA-256。無ければ空。"""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigError(f"{path.name}: 取り込みの記録として読めない: {e}") from e
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ConfigError(f"{path.name}: 取り込みの記録として読めない（名前と SHA-256 の組でない）")
    return data


def cmd_install(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    dirs = local_dirs(root)
    records: dict[str, dict[str, str]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / "selected"
        for char in args.chars:
            _check_name_part(char, "character")
            src = dirs.selected / char
            if not src.is_dir():
                raise ConfigError(f"{char}: 採用した絵が無い（{src}）")
            previous = _read_installed(_installed_record(dirs, char))
            # 退避したフォルダ（replaced/）や一時ファイルは持ち込まない。前回の取り込みの後に採用し直した絵だけを入れる
            # （前回入れたままの絵を入れると、その後に Colab の道などで直した source/ を古い採用に戻してしまう）
            # 先に写しを取り、写しの SHA-256 で判定・記録する（写す前後に別の adopt が置き換えても、記録と取り込んだ絵が食い違わない）
            (staged / char).mkdir(parents=True)
            fresh: dict[str, str] = {}
            for f in sorted(src.iterdir()):
                if not f.is_file() or f.name.startswith("."):
                    continue
                copy = staged / char / f.name
                shutil.copy2(f, copy)
                sha = file_sha256(copy)
                if previous.get(f.name) == sha:
                    copy.unlink()
                else:
                    fresh[f.name] = sha
            if not fresh:
                raise ConfigError(f"{char}: 前回の取り込みの後に採用し直した絵が無い（{src}）")
            # 取り込みは source/ を丸ごと置き換える。採用し直していない絵（顔・全身・表情）は今の source/ から持ち越す。
            # ただし顔を採用し直したときは、表情（face_*.png）を持ち越さない（古い顔から作ったので検査で落ちる）
            # 今の設定に無い名前（expressions から消した表情など）は持ち越さず、取り込みの「消した」に出す
            accepted = set(_accepted_names(list(load_character(root, char).expressions)))
            source_dir = root / "characters" / char / "source"
            if source_dir.is_dir():
                for kept in sorted(source_dir.iterdir()):
                    if not kept.is_file() or kept.name in fresh or kept.name not in accepted:
                        continue
                    if "face.png" in fresh and kept.name.startswith("face_"):
                        continue
                    shutil.copy2(kept, staged / char / kept.name)
            records[char] = {**previous, **fresh}
        reports = install_selection(root, staged)
    dirs.installed.mkdir(parents=True, exist_ok=True)
    for char, record in records.items():
        # 一時ファイルに書き終えてから置き換える（途中で失敗しても、前の完全な記録が残る）
        path = _installed_record(dirs, char)
        tmp_path = path.with_name(f".{path.name}.tmp")
        try:
            tmp_path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8",
            )
            os.replace(tmp_path, path)
        finally:
            tmp_path.unlink(missing_ok=True)
    print_reports(reports)


_NO_MATTE = "候補の背景を消さずにページを作る（既定では Modal で消して、隣に並べる）"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m artgen.cloud", description="Modal で作った候補を扱う")
    parser.add_argument("--root", type=Path, default=Path("."))
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("generate", help="ジョブのファイルから Modal で生成する")
    p.add_argument("--jobs", type=Path, required=True)
    p.add_argument("--no-matte", action="store_true", help=_NO_MATTE)
    p.set_defaults(func=cmd_generate)
    p = sub.add_parser("page", help="候補のページを作り直す")
    p.add_argument("round_json", type=Path)
    p.add_argument("--no-matte", action="store_true", help=_NO_MATTE)
    p.set_defaults(func=cmd_page)
    p = sub.add_parser("merge", help="回りの記録をまとめ、通し番号の記録とページを作る")
    p.add_argument("rounds", nargs="+", type=Path)
    p.add_argument("--no-matte", action="store_true", help=_NO_MATTE)
    p.set_defaults(func=cmd_merge)
    p = sub.add_parser("matte", help="切り出しの元の絵の背景のマスクを Modal で作る")
    p.add_argument("chars", nargs="+")
    p.set_defaults(func=cmd_matte)
    p = sub.add_parser("adopt", help="番号の候補を採用する")
    p.add_argument("round_json", type=Path)
    p.add_argument("number", type=int)
    p.add_argument("--flip", action="store_true", help="顔を左右反転して採用する")
    p.set_defaults(func=cmd_adopt)
    p = sub.add_parser("install", help="採用した絵を characters/<id>/source/ に取り込む")
    p.add_argument("chars", nargs="+")
    p.set_defaults(func=cmd_install)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except _STOPS as e:
        print(f"止まった: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
