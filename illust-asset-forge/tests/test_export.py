import hashlib
import io
import json

import pytest
import yaml
from PIL import Image

from artgen.config import ConfigError, load_character
from artgen.export import ExportError, check_dir, cutout_record, export_character, main
from artgen.matte import MODEL_SHA256, save_mattes
from artgen.pnginfo import MissingParamsError, read_params, save_png


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


CHARACTER_YAML = (
    "name: C\nstyle: s\nsubject: [1boy]\nappearance: []\noutfit: []\n"
    "default_expression: normal\nexpressions: {normal: [serious], hurt: [pain]}\n"
)


@pytest.fixture
def repo(tmp_path):
    write(tmp_path, "styles/s.yaml", "prompt: [masterpiece]\nnegative: [lowres]\n")
    write(tmp_path, "templates/face.yaml",
          "width: 1024\nheight: 1024\nprompt: [portrait]\nnegative: []\nexport_size: 256\n")
    write(tmp_path, "templates/fullbody.yaml",
          "width: 832\nheight: 1216\nprompt: [full body]\nnegative: []\nexport_size: null\n")
    write(tmp_path, "characters/c1/character.yaml", CHARACTER_YAML)
    return tmp_path


def put(repo, name, size, template, seed=1, params=True):
    path = repo / "characters/c1/source" / name
    image = Image.new("RGB", size, (10, 20, 30))
    if params:
        save_png(image, path, {"seed": seed, "template": template, "prompt": "騎士"})
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
    return path


def test_face_is_resized_to_256(repo):
    put(repo, "face.png", (1024, 1024), "face")
    export_character(repo, "c1")
    out = repo / "characters/c1/face.png"
    assert Image.open(out).size == (256, 256)
    with pytest.raises(MissingParamsError):
        read_params(out)


def test_expression_face_and_fullbody(repo):
    src = put(repo, "fullbody.png", (832, 1216), "fullbody")
    put(repo, "face_hurt.png", (1024, 1024), "face")
    export_character(repo, "c1")
    assert Image.open(repo / "characters/c1/face_hurt.png").size == (256, 256)
    out = repo / "characters/c1/fullbody.png"
    assert Image.open(out).size == (832, 1216)
    assert out.read_bytes() == src.read_bytes()


def test_params_json(repo):
    put(repo, "face.png", (1024, 1024), "face", seed=11)
    put(repo, "fullbody.png", (832, 1216), "fullbody")
    paths = export_character(repo, "c1")
    text = (repo / "characters/c1/params.json").read_text(encoding="utf-8")
    data = json.loads(text)
    assert list(data) == ["face.png", "fullbody.png"]
    assert data["face.png"]["seed"] == 11
    assert "騎士" in text and text.endswith("\n")
    assert repo / "characters/c1/params.json" in paths


def test_rejects_unknown_name(repo):
    put(repo, "face_laugh.png", (1024, 1024), "face")
    with pytest.raises(ExportError) as e:
        export_character(repo, "c1")
    assert "face_laugh.png" in str(e.value)
    assert "face_hurt.png" in str(e.value)


def test_rejects_non_square_face(repo):
    put(repo, "face.png", (1024, 1000), "face")
    with pytest.raises(ExportError):
        export_character(repo, "c1")


def test_missing_params(repo):
    put(repo, "face.png", (1024, 1024), "face", params=False)
    with pytest.raises(MissingParamsError):
        export_character(repo, "c1")


def test_missing_template_key_in_params(repo):
    path = repo / "characters/c1/source/face.png"
    save_png(Image.new("RGB", (1024, 1024)), path, {"seed": 1})
    with pytest.raises(ExportError) as e:
        export_character(repo, "c1")
    assert "template" in str(e.value)


def test_unknown_template_in_params(repo):
    put(repo, "face.png", (1024, 1024), "nonexistent")
    with pytest.raises(ConfigError):
        export_character(repo, "c1")


def test_nothing_written_when_any_file_is_bad(repo):
    put(repo, "face.png", (1024, 1024), "face")
    put(repo, "face_hurt.png", (1024, 1024), "face", params=False)
    with pytest.raises(MissingParamsError):
        export_character(repo, "c1")
    assert not (repo / "characters/c1/face.png").exists()
    assert not (repo / "characters/c1/params.json").exists()


def test_empty_or_missing_source(repo):
    with pytest.raises(ExportError):
        export_character(repo, "c1")
    (repo / "characters/c1/source").mkdir()
    with pytest.raises(ExportError):
        export_character(repo, "c1")


def test_cli_exit_code(repo, capsys):
    put(repo, "face.png", (1024, 1024), "face")
    assert main(["c1", "--root", str(repo)]) == 0
    write(repo, "characters/c2/character.yaml",
          "name: D\nstyle: s\nsubject: []\nappearance: []\noutfit: []\n"
          "default_expression: normal\nexpressions: {normal: []}\n")
    assert main(["c2", "--root", str(repo)]) == 1
    assert "source" in capsys.readouterr().out
    assert main(["nobody", "--root", str(repo)]) == 1


def test_rejects_image_whose_template_does_not_match_name(repo):
    put(repo, "fullbody.png", (1024, 1024), "face")  # face の絵を fullbody と名付けた
    with pytest.raises(ExportError) as e:
        export_character(repo, "c1")
    assert "fullbody.png" in str(e.value) and "template" in str(e.value)


def put_full(repo, name, size, **params):
    save_png(Image.new("RGB", size), repo / "characters/c1/source" / name,
             {"template": "face", "seed": 1, **params})


def test_rejects_expression_mismatch(repo):
    put_full(repo, "face.png", (1024, 1024), expression="hurt")
    with pytest.raises(ExportError) as e:
        export_character(repo, "c1")
    assert "expression" in str(e.value)


def test_accepts_matching_expression(repo):
    put_full(repo, "face.png", (1024, 1024), expression="normal", character="c1")
    put_full(repo, "face_hurt.png", (1024, 1024), expression="hurt", character="c1")
    export_character(repo, "c1")


def test_rejects_character_mismatch(repo):
    put_full(repo, "face.png", (1024, 1024), character="someone-else")
    with pytest.raises(ExportError) as e:
        export_character(repo, "c1")
    assert "character" in str(e.value)


def test_rejects_downscaled_attachment(repo):
    put_full(repo, "face.png", (512, 512), width=1024, height=1024)
    with pytest.raises(ExportError) as e:
        export_character(repo, "c1")
    assert "縮め" in str(e.value)


@pytest.mark.parametrize("name", ["face.PNG", "face_hurt.jpg", "notes.txt"])
def test_rejects_non_png_or_odd_extension(repo, name):
    put(repo, "face.png", (1024, 1024), "face")
    (repo / "characters/c1/source" / name).write_bytes(b"x")
    with pytest.raises(ExportError) as e:
        export_character(repo, "c1")
    assert name in str(e.value)


def test_hidden_files_in_source_are_ignored(repo):
    put(repo, "face.png", (1024, 1024), "face")
    (repo / "characters/c1/source/.DS_Store").write_bytes(b"x")
    export_character(repo, "c1")


def test_stale_outputs_are_removed(repo):
    put(repo, "face.png", (1024, 1024), "face")
    stale = repo / "characters/c1/face_hurt.png"
    Image.new("RGB", (256, 256)).save(stale)
    export_character(repo, "c1")
    assert not stale.exists()
    assert list(json.loads((repo / "characters/c1/params.json").read_text(encoding="utf-8"))) == ["face.png"]


# --- cutouts ---

def set_cutouts(repo, cutouts, base=CHARACTER_YAML):
    text = base if cutouts is None else base + yaml.safe_dump({"cutouts": cutouts}, allow_unicode=True)
    write(repo, "characters/c1/character.yaml", text)


def two_outputs(background="none", **extra):
    return {
        "background": background,
        "outputs": [
            {"suffix": "", "box": [0, 0, 1024, 1024], "width": 256},
            {"suffix": "-small", "box": [256, 256, 768, 768], "width": 128},
        ],
        **extra,
    }


def png_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def half_mask(size=(1024, 1024)):
    mask = Image.new("L", size, 255)
    mask.paste(0, (size[0] // 2, 0, size[0], size[1]))
    return mask


def make_matte(repo, names, mask=None):
    save_mattes(repo, "c1", {n: png_bytes(mask or half_mask()) for n in names}, MODEL_SHA256)


def snapshot(repo):
    base = repo / "characters/c1"
    return {p.name: p.read_bytes() for p in base.iterdir() if p.is_file() and p.name != "character.yaml"}


def test_export_without_cutouts_is_unchanged(repo):
    put(repo, "face.png", (1024, 1024), "face")
    put(repo, "fullbody.png", (832, 1216), "fullbody")
    export_character(repo, "c1")
    assert Image.open(repo / "characters/c1/face.png").mode == "RGB"
    assert Image.open(repo / "characters/c1/face.png").size == (256, 256)
    assert (repo / "characters/c1/fullbody.png").read_bytes() == (repo / "characters/c1/source/fullbody.png").read_bytes()
    assert "cutouts" not in json.loads((repo / "characters/c1/params.json").read_text(encoding="utf-8"))
    assert not (repo / "local/check/c1").exists()


def test_export_cutouts_write_each_output_as_rgba(repo):
    put(repo, "face.png", (1024, 1024), "face")
    put(repo, "face_hurt.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": two_outputs()})
    export_character(repo, "c1")
    for name, size in [("face.png", 256), ("face-small.png", 128), ("face_hurt.png", 256), ("face_hurt-small.png", 128)]:
        im = Image.open(repo / "characters/c1" / name)
        assert im.mode == "RGBA" and im.size == (size, size), name


def test_export_cutout_width_keeps_box_ratio(repo):
    put(repo, "fullbody.png", (832, 1216), "fullbody")
    set_cutouts(repo, {"fullbody": {"background": "none", "outputs": [{"suffix": "", "box": [0, 0, 400, 600], "width": 200}]}})
    export_character(repo, "c1")
    assert Image.open(repo / "characters/c1/fullbody.png").size == (200, 300)


def test_export_matte_uses_mask_and_erase(repo):
    put(repo, "face.png", (1024, 1024), "face")
    make_matte(repo, ["face.png"])
    cfg = {"background": "matte", "erase": [[[0, 0], [200, 0], [200, 200]]], "outputs": [{"suffix": "", "width": 256}]}
    set_cutouts(repo, {"face": cfg})
    export_character(repo, "c1")
    out = Image.open(repo / "characters/c1/face.png")
    assert out.getpixel((20, 100))[3] == 255
    assert out.getpixel((200, 100))[3] == 0
    assert out.getpixel((8, 2))[3] == 0  # erase の多角形の中


def test_export_stops_when_matte_is_missing(repo):
    put(repo, "face.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": two_outputs("matte")})
    with pytest.raises(ExportError, match="python -m artgen.cloud matte c1"):
        export_character(repo, "c1")


def test_export_stops_when_matte_is_older_than_source(repo):
    put(repo, "face.png", (1024, 1024), "face")
    make_matte(repo, ["face.png"])
    put(repo, "face.png", (1024, 1024), "face", seed=99)
    set_cutouts(repo, {"face": two_outputs("matte")})
    with pytest.raises(ExportError, match="古い.*cloud matte c1"):
        export_character(repo, "c1")


def test_export_writes_nothing_when_one_variant_matte_is_stale(repo):
    put(repo, "face.png", (1024, 1024), "face")
    put(repo, "face_hurt.png", (1024, 1024), "face")
    make_matte(repo, ["face.png", "face_hurt.png"])
    set_cutouts(repo, {"face": two_outputs("matte")})
    export_character(repo, "c1")
    before = snapshot(repo)
    put(repo, "face_hurt.png", (1024, 1024), "face", seed=99)  # 表情だけ差し替えた
    set_cutouts(repo, {"face": {**two_outputs("matte"), "outputs": [{"suffix": "", "width": 100}]}})
    with pytest.raises(ExportError, match="face_hurt.png"):
        export_character(repo, "c1")
    assert snapshot(repo) == before


def test_export_stops_when_box_is_outside_image(repo):
    put(repo, "face.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": {"background": "none", "outputs": [{"suffix": "", "box": [0, 0, 2000, 100]}]}})
    with pytest.raises(ConfigError, match=r"cutouts\.face\.outputs\[0\]\.box"):
        export_character(repo, "c1")


def test_export_stops_when_outputs_collide(repo):
    base = CHARACTER_YAML.replace("hurt: [pain]", "normal-small: [x]")
    put(repo, "face_normal.png", (1024, 1024), "face")
    put(repo, "face_normal-small.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": two_outputs()}, base=base)
    with pytest.raises(ExportError, match="同じ名前"):
        export_character(repo, "c1")


def test_export_removes_outputs_of_removed_cutouts(repo):
    put(repo, "face.png", (1024, 1024), "face")
    put(repo, "face_hurt.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": two_outputs()})
    export_character(repo, "c1")
    assert (repo / "characters/c1/face-small.png").exists()
    set_cutouts(repo, None)
    export_character(repo, "c1")
    assert not (repo / "characters/c1/face-small.png").exists()
    assert not (repo / "characters/c1/face_hurt-small.png").exists()
    assert not list((repo / "local/check/c1").glob("*.png"))
    out = Image.open(repo / "characters/c1/face.png")
    assert out.mode == "RGB" and out.size == (256, 256)


def test_export_records_cutouts_in_params(repo):
    put(repo, "face.png", (1024, 1024), "face")
    make_matte(repo, ["face.png"])
    set_cutouts(repo, {"face": two_outputs("matte", erase=[[[0, 0], [9, 0], [9, 9]]])})
    export_character(repo, "c1")
    params = json.loads((repo / "characters/c1/params.json").read_text(encoding="utf-8"))
    character = load_character(repo, "c1")
    expected = cutout_record(character.cutouts["face"], repo / "characters/c1/source", ["face.png"])
    assert params["cutouts"] == {"face": expected}
    assert expected["matte_sha256"]["face.png"] == hashlib.sha256((repo / "characters/c1/matte/face.png").read_bytes()).hexdigest()
    assert expected["outputs"][1] == {"suffix": "-small", "box": [256, 256, 768, 768], "width": 128}
    assert expected["erase"] == [[[0, 0], [9, 0], [9, 9]]]


def test_export_writes_check_images(repo):
    put(repo, "face.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": two_outputs()})
    export_character(repo, "c1")
    check = check_dir(repo, "c1")
    assert Image.open(check / "face.png").size == (1024, 1024)
    assert Image.open(check / "face-small.png").size == (512, 512)


def test_export_removes_outputs_of_removed_expression(repo):
    put(repo, "face.png", (1024, 1024), "face")
    put(repo, "face_hurt.png", (1024, 1024), "face")
    set_cutouts(repo, {"face": two_outputs()})
    export_character(repo, "c1")
    assert (repo / "characters/c1/face_hurt-small.png").exists()
    (repo / "characters/c1/source/face_hurt.png").unlink()
    set_cutouts(repo, {"face": two_outputs()}, base=CHARACTER_YAML.replace("hurt: [pain]", "shout: [x]"))
    export_character(repo, "c1")
    assert not (repo / "characters/c1/face_hurt.png").exists()
    assert not (repo / "characters/c1/face_hurt-small.png").exists()
    assert (repo / "characters/c1/face.png").exists()


def test_export_stops_with_one_line_when_matte_json_is_broken(repo):
    put(repo, "face.png", (1024, 1024), "face")
    make_matte(repo, ["face.png"])
    (repo / "characters/c1/matte/matte.json").write_text("{broken", encoding="utf-8")
    set_cutouts(repo, {"face": two_outputs("matte")})
    with pytest.raises(ExportError, match="matte.json.*cloud matte c1"):
        export_character(repo, "c1")


def test_export_records_sha_of_the_source_it_rendered(repo, monkeypatch):
    import artgen.export as E

    path = put(repo, "face.png", (1024, 1024), "face")
    make_matte(repo, ["face.png"])
    set_cutouts(repo, {"face": two_outputs("matte")})
    rendered_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    real_render = E.render
    swapped = []

    def render_then_swap(*args, **kwargs):
        if not swapped:  # 描画のあいだに、別の処理が元の絵を差し替えた
            swapped.append(True)
            put(repo, "face.png", (1024, 1024), "face", seed=99)
        return real_render(*args, **kwargs)

    monkeypatch.setattr(E, "render", render_then_swap)
    export_character(repo, "c1")
    params = json.loads((repo / "characters/c1/params.json").read_text(encoding="utf-8"))
    assert params["cutouts"]["face"]["source_sha256"]["face.png"] == rendered_sha


def test_export_ignores_broken_previous_params(repo):
    put(repo, "face.png", (1024, 1024), "face")
    (repo / "characters/c1/params.json").write_text("[1]", encoding="utf-8")
    export_character(repo, "c1")
    assert list(json.loads((repo / "characters/c1/params.json").read_text(encoding="utf-8"))) == ["face.png"]


def test_export_stops_when_output_height_would_be_zero(repo):
    put(repo, "fullbody.png", (2000, 2), "fullbody")
    set_cutouts(repo, {"fullbody": {"background": "none", "outputs": [{"suffix": "", "width": 10}]}})
    with pytest.raises(ConfigError, match=r"cutouts\.fullbody\.outputs\[0\]\.width"):
        export_character(repo, "c1")
