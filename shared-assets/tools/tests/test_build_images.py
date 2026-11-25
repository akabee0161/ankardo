import json
from pathlib import Path

import pytest
from PIL import Image

import build_images


def make_forge(root: Path, ids: list[str]) -> None:
    for i in ids:
        d = root / "characters" / i
        d.mkdir(parents=True)
        # 四隅は透明、中央は不透明な赤の四角（絵が消えたり、透明になったりしないかを見るため）
        im = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        im.paste((200, 40, 40, 255), (156, 156, 356, 356))
        im.save(d / "object.png")


def make_items(path: Path, ids: list[str]) -> Path:
    items = {
        "categories": [{"key": "animal", "label": "どうぶつ"}],
        "items": [{"id": i, "category": "animal", "label": i, "kana": "あ", "reading": "あ"} for i in ids],
    }
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return path


def test_writes_webp_with_alpha(tmp_path):
    make_forge(tmp_path / "forge", ["a", "b"])
    items = make_items(tmp_path / "items.json", ["a", "b"])
    out = tmp_path / "img"
    written = build_images.main(tmp_path / "forge", out, items)
    assert sorted(p.name for p in written) == ["a.webp", "b.webp"]
    for p in written:
        im = Image.open(p)
        assert im.format == "WEBP" and im.size == (512, 512)
        rgba = im.convert("RGBA")
        assert rgba.getpixel((0, 0))[3] == 0
        assert rgba.getpixel((511, 511))[3] == 0
        # 絵の部分は、不透明のまま、ほぼ同じ色で残る（webp の圧縮で少しずれてよい）
        r, g, b, a = rgba.getpixel((256, 256))
        assert a == 255
        assert abs(r - 200) <= 12 and abs(g - 40) <= 12 and abs(b - 40) <= 12, (r, g, b)


def test_stops_when_image_missing(tmp_path):
    make_forge(tmp_path / "forge", ["a"])
    items = make_items(tmp_path / "items.json", ["a", "b"])
    out = tmp_path / "img"
    with pytest.raises(build_images.BuildError) as e:
        build_images.main(tmp_path / "forge", out, items)
    assert "b" in str(e.value)
    assert not out.exists() or not any(out.iterdir())


def test_removed_items_do_not_leave_old_webp(tmp_path):
    make_forge(tmp_path / "forge", ["a", "b"])
    out = tmp_path / "img"
    build_images.main(tmp_path / "forge", out, make_items(tmp_path / "items.json", ["a", "b"]))
    build_images.main(tmp_path / "forge", out, make_items(tmp_path / "items.json", ["a"]))
    assert [p.name for p in out.iterdir()] == ["a.webp"]


def test_rejects_wrong_size_image(tmp_path):
    make_forge(tmp_path / "forge", ["a"])
    Image.new("RGBA", (100, 100)).save(tmp_path / "forge" / "characters" / "a" / "object.png")
    items = make_items(tmp_path / "items.json", ["a"])
    with pytest.raises(build_images.BuildError):
        build_images.main(tmp_path / "forge", tmp_path / "img", items)
