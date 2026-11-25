"""forge の書き出した絵（characters/<id>/object.png）を、共通素材の img/<id>.webp にする。

使い方（ankardo のルートで）:
    illust-asset-forge/.venv/bin/python shared-assets/tools/build_images.py

items.json にある ID の絵が 1 つでも無い・大きさが違うときは、何も書かずに止まる。
img/ は items.json の ID と同じ構成に置き換える（items.json から外れた ID の古い webp は消す）。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

SIZE = 512
QUALITY = 90

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FORGE = ROOT / "illust-asset-forge"
DEFAULT_OUT = ROOT / "shared-assets" / "chiiku" / "img"
DEFAULT_ITEMS = ROOT / "shared-assets" / "chiiku" / "items.json"


class BuildError(Exception):
    """絵を書き出せない入力（絵が無い・大きさが違う・items.json が読めない）。"""


def _item_ids(items_path: Path) -> list[str]:
    try:
        data = json.loads(Path(items_path).read_text(encoding="utf-8"))
        return [item["id"] for item in data["items"]]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        raise BuildError(f"{items_path}: items.json として読めない: {e}") from e


def main(forge_root: Path, out_dir: Path, items_path: Path) -> list[Path]:
    forge_root, out_dir = Path(forge_root), Path(out_dir)
    ids = _item_ids(items_path)

    # 何も書く前に、全部の絵を検査する
    sources: dict[str, Path] = {}
    missing = []
    for item_id in ids:
        src = forge_root / "characters" / item_id / "object.png"
        if not src.is_file():
            missing.append(item_id)
        else:
            sources[item_id] = src
    if missing:
        raise BuildError(f"絵が無い（characters/<id>/object.png）: {', '.join(missing)}")
    for item_id, src in sources.items():
        with Image.open(src) as im:
            if im.size != (SIZE, SIZE):
                raise BuildError(f"{src}: {im.width}x{im.height}（{SIZE}x{SIZE} でない）")

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.webp"):
        if old.stem not in sources:
            old.unlink()
    written = []
    for item_id, src in sources.items():
        dest = out_dir / f"{item_id}.webp"
        with Image.open(src) as im:
            im.convert("RGBA").save(dest, format="WEBP", quality=QUALITY)
        written.append(dest)
    return written


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="forge の絵を共通素材の webp にする")
    parser.add_argument("--forge", type=Path, default=DEFAULT_FORGE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--items", type=Path, default=DEFAULT_ITEMS)
    args = parser.parse_args(argv)
    try:
        written = main(args.forge, args.out, args.items)
    except BuildError as e:
        print(f"止まった: {e}")
        return 1
    for p in written:
        print(f"書き出した: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
