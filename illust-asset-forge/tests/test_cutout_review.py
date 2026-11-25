import base64
import io
import re
import shutil

import pytest
from PIL import Image

from artgen.cutout_review import build_review, build_reviews, main
from artgen.export import ExportError, export_character
from test_export import CHARACTER_YAML, make_matte, put, repo, set_cutouts, two_outputs, write  # noqa: F401


@pytest.fixture
def exported(repo):
    put(repo, "face.png", (1024, 1024), "face")
    put(repo, "face_hurt.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": two_outputs()})
    export_character(repo, "c1")
    return repo


def _framed(html):
    m = re.search(r'alt="元の絵（範囲の枠つき）"[^>]*src="data:image/png;base64,([^"]+)"', html)
    return Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("RGB")


def test_review_shows_each_output_with_box_and_check(exported):
    path = build_review(exported, "c1")
    assert path == exported / "local/check/c1/review.html"
    html = path.read_text(encoding="utf-8")
    assert "face.png（256x256）" in html and "face-small.png（128x128）" in html
    framed = _framed(html)
    colors = {c for _, c in framed.getcolors(512 * 512)}
    assert (255, 0, 0) in colors and (0, 112, 255) in colors


def test_review_hides_variants_by_default(exported):
    html = build_review(exported, "c1").read_text(encoding="utf-8")
    assert "face_hurt" not in html


def test_review_shows_variants_when_asked(exported):
    html = build_review(exported, "c1", variants=True).read_text(encoding="utf-8")
    assert "face_hurt-small.png" in html and "face_hurt.png（256x256）" in html


def test_review_stops_without_export(repo):
    put(repo, "face.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": two_outputs()})
    with pytest.raises(ExportError, match="python -m artgen.export"):
        build_review(repo, "c1")


def test_review_stops_without_cutouts(exported):
    set_cutouts(exported, None)
    with pytest.raises(ExportError, match="cutouts が無い"):
        build_review(exported, "c1")


def test_review_stops_when_config_changed_after_export(exported):
    changed = two_outputs()
    changed["outputs"][0]["box"] = [0, 0, 900, 900]
    set_cutouts(exported, {"face": changed})
    with pytest.raises(ExportError, match="python -m artgen.export"):
        build_review(exported, "c1")


def test_review_stops_when_matte_changed_after_export(repo):
    put(repo, "face.png", (1024, 1024), "face")
    make_matte(repo, ["face.png"])
    set_cutouts(repo, {"face": two_outputs("matte")})
    export_character(repo, "c1")
    build_review(repo, "c1")
    make_matte(repo, ["face.png"], Image.new("L", (1024, 1024), 255))  # マスクを作り直した
    with pytest.raises(ExportError, match="python -m artgen.export"):
        build_review(repo, "c1")


def test_review_checks_variants_even_when_hidden(exported):
    put(exported, "face_hurt.png", (1024, 1024), "face", seed=99)
    with pytest.raises(ExportError, match="python -m artgen.export"):
        build_review(exported, "c1", variants=False)


def test_review_stops_when_a_source_was_added_after_export(exported):
    (exported / "characters/c1/source/face_hurt.png").unlink()
    export_character(exported, "c1")
    put(exported, "face_hurt.png", (1024, 1024), "face")
    with pytest.raises(ExportError, match="python -m artgen.export"):
        build_review(exported, "c1")


@pytest.fixture
def two_exported(exported):
    write(exported, "characters/c2/character.yaml", CHARACTER_YAML.replace("name: C\n", "name: D\n"))
    set_cutouts_for(exported, "c2")
    (exported / "characters/c2/source").mkdir(parents=True)
    shutil.copy2(exported / "characters/c1/source/face.png", exported / "characters/c2/source/face.png")
    export_character(exported, "c2")
    return exported


def set_cutouts_for(repo, char):
    import yaml

    path = repo / f"characters/{char}/character.yaml"
    path.write_text(path.read_text(encoding="utf-8") + yaml.safe_dump({"cutouts": {"face": two_outputs()}}), encoding="utf-8")


def test_reviews_one_page_or_nothing(two_exported):
    out = two_exported / "local/check/reviews/t.html"
    html = build_reviews(two_exported, ["c1", "c2"], out).read_text(encoding="utf-8")
    assert "C（c1）" in html and "D（c2）" in html
    assert html.count("data:image/jpeg;base64,") == 8  # 1 人 4 枚（枠あり・枠なし・確認図 2）
    assert html.count("data:image/png;base64,") >= 4  # 書き出した絵は PNG のまま
    out.unlink()
    # c2 だけ古い
    set_cutouts_for_changed = two_outputs()
    set_cutouts_for_changed["outputs"][0]["width"] = 100
    write(two_exported, "characters/c2/character.yaml", CHARACTER_YAML.replace("name: C\n", "name: D\n"))
    import yaml

    p = two_exported / "characters/c2/character.yaml"
    p.write_text(p.read_text(encoding="utf-8") + yaml.safe_dump({"cutouts": {"face": set_cutouts_for_changed}}), encoding="utf-8")
    with pytest.raises(ExportError, match="c2"):
        build_reviews(two_exported, ["c1", "c2"], out)
    assert not out.exists()


def test_reviews_default_path_is_under_check_reviews(two_exported):
    out = build_reviews(two_exported, ["c1", "c2"])
    assert out.parent == two_exported / "local/check/reviews" and out.suffix == ".html"


def test_review_preview_section_only_with_preview_background(exported):
    html = build_review(exported, "c1").read_text(encoding="utf-8")
    assert '<div class="preview"' not in html
    write(exported, "defaults.yaml", 'style: s\npreview_background: "#3366aa"\n')
    html = build_review(exported, "c1").read_text(encoding="utf-8")
    assert '<div class="preview"' in html and "#3366aa" in html


def test_main_prints_path_or_error(exported, capsys):
    assert main(["c1", "--root", str(exported)]) == 0
    assert "作った:" in capsys.readouterr().out
    assert main(["nobody", "--root", str(exported)]) == 1
    assert capsys.readouterr().out.startswith("作れない:")
    out = exported / "local/check/reviews/x.html"
    assert main(["c1", "--root", str(exported), "--out", str(out), "--variants"]) == 0
    assert out.is_file() and "face_hurt" in out.read_text(encoding="utf-8")


def test_review_removes_old_page_when_check_fails(exported):
    path = build_review(exported, "c1")
    assert path.is_file()
    changed = two_outputs()
    changed["outputs"][0]["box"] = [0, 0, 900, 900]
    set_cutouts(exported, {"face": changed})
    with pytest.raises(ExportError):
        build_review(exported, "c1")
    assert not path.exists()  # 古い範囲のページを承認に出さない


def test_reviews_remove_old_page_at_out_when_check_fails(two_exported):
    import yaml

    out = two_exported / "local/check/reviews/t.html"
    build_reviews(two_exported, ["c1", "c2"], out)
    assert out.is_file()
    changed = two_outputs()
    changed["outputs"][0]["width"] = 100
    p = two_exported / "characters/c2/character.yaml"
    write(two_exported, "characters/c2/character.yaml", CHARACTER_YAML.replace("name: C\n", "name: D\n"))
    p.write_text(p.read_text(encoding="utf-8") + yaml.safe_dump({"cutouts": {"face": changed}}), encoding="utf-8")
    with pytest.raises(ExportError, match="c2"):
        build_reviews(two_exported, ["c1", "c2"], out)
    assert not out.exists()
