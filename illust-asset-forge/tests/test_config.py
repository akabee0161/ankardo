import re
from pathlib import Path

import pytest

from artgen.config import (
    ClearColor,
    ConfigError,
    CutoutOutput,
    load_character,
    load_default_style,
    load_preview_background,
    load_style,
    load_template,
)

CHARACTER_YAML = """\
name: 騎士
style: color-anime
subject: [1boy, solo]
appearance: [brown hair]
outfit: [armor]
default_expression: normal
expressions:
  normal: [serious]
  hurt: [pain]
inpaint_box: null
"""

TEMPLATE_YAML = """\
width: 1024
height: 1024
prompt: [portrait]
negative: [full body]
export_size: 256
"""


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_character(root: Path, text: str = CHARACTER_YAML, char_id: str = "c1") -> None:
    write(root, f"characters/{char_id}/character.yaml", text)


def test_load_character_reads_all_fields(tmp_path):
    write_character(tmp_path)
    c = load_character(tmp_path, "c1")
    assert c.id == "c1"
    assert c.name == "騎士"
    assert c.style == "color-anime"
    assert c.subject == ["1boy", "solo"]
    assert c.appearance == ["brown hair"]
    assert c.outfit == ["armor"]
    assert c.default_expression == "normal"
    assert c.expressions["hurt"] == ["pain"]
    assert c.inpaint_box is None
    assert c.items == []
    assert c.negative == []


def test_load_character_reads_inpaint_box(tmp_path):
    write_character(tmp_path, CHARACTER_YAML.replace("inpaint_box: null", "inpaint_box: [1, 2, 30, 40]"))
    assert load_character(tmp_path, "c1").inpaint_box == (1, 2, 30, 40)


def test_load_template_defaults(tmp_path):
    write(tmp_path, "templates/face.yaml", TEMPLATE_YAML)
    t = load_template(tmp_path, "face")
    assert t.width == 1024 and t.height == 1024
    assert t.export_size == 256
    assert t.steps == 28
    assert t.guidance == 5
    assert t.use_items is False
    assert t.inpaint_strength is None
    assert t.inpaint_feather is None


def test_load_template_inpaint_and_null_export(tmp_path):
    write(
        tmp_path,
        "templates/face.yaml",
        TEMPLATE_YAML.replace("export_size: 256", "export_size: null")
        + "inpaint: {strength: 0.6, feather: 24}\nuse_items: true\n",
    )
    t = load_template(tmp_path, "face")
    assert t.export_size is None
    assert t.inpaint_strength == 0.6
    assert t.inpaint_feather == 24
    assert t.use_items is True


def test_load_style(tmp_path):
    write(tmp_path, "styles/s.yaml", "prompt: [masterpiece]\nnegative: [lowres]\n")
    s = load_style(tmp_path, "s")
    assert s.name == "s"
    assert s.prompt == ["masterpiece"]
    assert s.negative == ["lowres"]


def test_missing_file_names_path(tmp_path):
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "nobody")
    assert "characters/nobody/character.yaml" in str(e.value)


def test_tags_must_be_list_of_strings(tmp_path):
    write_character(tmp_path, CHARACTER_YAML.replace("hurt: [pain]", 'hurt: "pain"'))
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "c1")
    assert "expressions.hurt" in str(e.value)
    assert "characters/c1/character.yaml" in str(e.value)


def test_default_expression_must_exist(tmp_path):
    write_character(tmp_path, CHARACTER_YAML.replace("default_expression: normal", "default_expression: smile"))
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "c1")
    msg = str(e.value)
    assert "default_expression" in msg
    assert "normal" in msg and "hurt" in msg


@pytest.mark.parametrize("box", ["[10, 10, 5, 20]", "[1, 2, 3]"])
def test_inpaint_box_shape(tmp_path, box):
    write_character(tmp_path, CHARACTER_YAML.replace("inpaint_box: null", f"inpaint_box: {box}"))
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "c1")
    assert "inpaint_box" in str(e.value)


def test_missing_required_key(tmp_path):
    write_character(tmp_path, CHARACTER_YAML.replace("name: 騎士\n", ""))
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "c1")
    assert "characters/c1/character.yaml: name: " in str(e.value)


NO_STYLE_YAML = CHARACTER_YAML.replace("style: color-anime\n", "")


def test_character_without_style_uses_default(tmp_path):
    write(tmp_path, "defaults.yaml", "style: flat\n")
    write_character(tmp_path, NO_STYLE_YAML)
    assert load_character(tmp_path, "c1").style == "flat"
    assert load_default_style(tmp_path) == "flat"


def test_character_style_overrides_default(tmp_path):
    write(tmp_path, "defaults.yaml", "style: flat\n")
    write_character(tmp_path)
    assert load_character(tmp_path, "c1").style == "color-anime"


def test_character_without_style_and_no_defaults_fails(tmp_path):
    write_character(tmp_path, NO_STYLE_YAML)
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "c1")
    assert "defaults.yaml" in str(e.value) and "ファイルが無い" in str(e.value)


@pytest.mark.parametrize("text", ['style: ""\n', "style: [a]\n", "other: x\n"])
def test_defaults_style_must_be_string(tmp_path, text):
    write(tmp_path, "defaults.yaml", text)
    write_character(tmp_path, NO_STYLE_YAML)
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "c1")
    assert str(e.value).startswith("defaults.yaml: style: ")


def test_character_style_null_is_rejected(tmp_path):
    write(tmp_path, "defaults.yaml", "style: flat\n")
    write_character(tmp_path, CHARACTER_YAML.replace("style: color-anime", "style: null"))
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "c1")
    assert "characters/c1/character.yaml: style: " in str(e.value)


def test_invalid_yaml_and_non_mapping(tmp_path):
    write_character(tmp_path, "- just\n- a list\n")
    with pytest.raises(ConfigError):
        load_character(tmp_path, "c1")
    write_character(tmp_path, "name: [unclosed\n")
    with pytest.raises(ConfigError):
        load_character(tmp_path, "c1")


def test_template_size_must_be_positive_int(tmp_path):
    write(tmp_path, "templates/face.yaml", TEMPLATE_YAML.replace("width: 1024", "width: wide"))
    with pytest.raises(ConfigError) as e:
        load_template(tmp_path, "face")
    assert "width" in str(e.value)


def test_unbalanced_parens_in_tag_is_rejected_with_quoting_hint(tmp_path):
    # YAML の flow list では、カンマを含む重み付きタグが黙って割れる
    write_character(tmp_path, CHARACTER_YAML.replace("appearance: [brown hair]", "appearance: [(a, b:1.1)]"))
    with pytest.raises(ConfigError) as e:
        load_character(tmp_path, "c1")
    assert "appearance" in str(e.value) and "カッコ" in str(e.value) and "引用符" in str(e.value)


def test_quoted_weighted_tag_with_comma_is_accepted(tmp_path):
    write_character(tmp_path, CHARACTER_YAML.replace("appearance: [brown hair]", 'appearance: ["(a, b:1.1)"]'))
    assert load_character(tmp_path, "c1").appearance == ["(a, b:1.1)"]


def test_template_reads_inpaint_box(tmp_path):
    write(tmp_path, "templates/face.yaml",
          "width: 1024\nheight: 1024\nprompt: [p]\nnegative: []\n"
          "inpaint: {strength: 0.6, feather: 24, box: [300, 200, 700, 600]}\n")
    assert load_template(tmp_path, "face").inpaint_box == (300, 200, 700, 600)


@pytest.mark.parametrize("box", ["[1, 2, 3]", "[5, 5, 5, 9]", "[-1, 0, 10, 10]", "[0, 0, 1.5, 9]"])
def test_template_rejects_bad_inpaint_box(tmp_path, box):
    write(tmp_path, "templates/face.yaml",
          f"width: 1024\nheight: 1024\nprompt: [p]\nnegative: []\n"
          f"inpaint: {{strength: 0.6, feather: 24, box: {box}}}\n")
    with pytest.raises(ConfigError, match=r"templates/face.yaml: inpaint.box: "):
        load_template(tmp_path, "face")


# --- その場の画風（inline_style） ---------------------------------------


def test_inline_style_builds_style():
    from artgen.config import Style, inline_style

    s = inline_style({"name": "my-style_2", "prompt": ["flat color"], "negative": []})
    assert s == Style(name="my-style_2", prompt=["flat color"], negative=[])


def test_inline_style_negative_defaults_to_empty():
    from artgen.config import inline_style

    assert inline_style({"name": "a", "prompt": ["x"]}).negative == []


@pytest.mark.parametrize(
    "value, match",
    [
        ("soft", "辞書"),
        ({"prompt": ["x"]}, "name"),
        ({"name": "", "prompt": ["x"]}, "name"),
        ({"name": 3, "prompt": ["x"]}, "name"),
        ({"name": "a/b", "prompt": ["x"]}, "name"),
        ({"name": "..", "prompt": ["x"]}, "name"),
        ({"name": ".hid", "prompt": ["x"]}, "name"),
        ({"name": "あ", "prompt": ["x"]}, "name"),
        ({"name": "a", "prompt": []}, "prompt"),
        ({"name": "a"}, "prompt"),
        ({"name": "a", "prompt": ["x", ""]}, "prompt"),
        ({"name": "a", "prompt": ["x", 1]}, "prompt"),
        ({"name": "a", "prompt": ["(x"]}, "カッコ"),
        ({"name": "a", "prompt": ["x"], "negative": "lowres"}, "negative"),
        ({"name": "a", "prompt": ["x"], "negative": ["(y"]}, "カッコ"),
        ({"name": "a", "prompt": ["x"], "extra": 1}, "extra"),
    ],
)
def test_inline_style_rejects_bad_input(value, match):
    from artgen.config import inline_style

    with pytest.raises(ConfigError, match=match):
        inline_style(value)


# --- cutouts ---

FACE_CUTOUT = """\
cutouts:
  face:
    background: matte
    erase:
      - [[10, 20], [80, 20], [60, 90]]
    outputs:
      - {suffix: "", box: [212, 120, 812, 720], width: 256}
      - {suffix: "-small", box: [312, 180, 712, 580], width: 128}
  fullbody:
    background: none
    outputs:
      - {suffix: ""}
"""


@pytest.fixture
def repo(tmp_path):
    write(tmp_path, "templates/face.yaml", TEMPLATE_YAML)
    write(tmp_path, "templates/fullbody.yaml", TEMPLATE_YAML)
    write(tmp_path, "defaults.yaml", "style: color-anime\n")
    write_character(tmp_path)
    return tmp_path


def with_cutouts(repo, cutouts_yaml: str) -> None:
    write_character(repo, CHARACTER_YAML + cutouts_yaml)


def test_cutouts_are_read_per_template(repo):
    with_cutouts(repo, FACE_CUTOUT)
    c = load_character(repo, "c1")
    face = c.cutouts["face"]
    assert face.template == "face"
    assert face.background == "matte"
    assert face.erase == (((10, 20), (80, 20), (60, 90)),)
    assert face.outputs == (
        CutoutOutput("", (212, 120, 812, 720), 256),
        CutoutOutput("-small", (312, 180, 712, 580), 128),
    )
    assert c.cutouts["fullbody"].outputs == (CutoutOutput("", None, None),)
    assert c.cutouts["fullbody"].background == "none"


def test_character_without_cutouts_has_empty_dict(repo):
    assert load_character(repo, "c1").cutouts == {}


@pytest.mark.parametrize(
    "cutouts, where",
    [
        ("{weapon: {background: none, outputs: [{suffix: ''}]}}", "cutouts.weapon"),
        ("{face: {background: blur, outputs: [{suffix: ''}]}}", "cutouts.face.background"),
        ("{face: {background: matte, clear_colors: [{min: 200, max_rg: 10, max_gb: 10}], outputs: [{suffix: ''}]}}", "cutouts.face.clear_colors"),
        ("{face: {background: colors, erase: [[[0,0],[1,0],[1,1]]], outputs: [{suffix: ''}]}}", "cutouts.face.erase"),
        ("{face: {background: none, outputs: []}}", "cutouts.face.outputs"),
        ("{face: {background: none, outputs: [{suffix: ''}, {suffix: ''}]}}", "cutouts.face.outputs[1].suffix"),
        ("{face: {background: none, outputs: [{suffix: 'a/b'}]}}", "cutouts.face.outputs[0].suffix"),
        ("{face: {background: none, outputs: [{suffix: '', width: 0}]}}", "cutouts.face.outputs[0].width"),
        ("{face: {background: none, outputs: [{suffix: '', size: 3}]}}", "cutouts.face.outputs[0]"),
        ("{face: {background: colors, clear_colors: [{min: 200, max_rg: 10, max_gb: 10, min_rg: 20}], outputs: [{suffix: ''}]}}", "cutouts.face.clear_colors[0].min_rg"),
        ("{face: {background: none, mode: x, outputs: [{suffix: ''}]}}", "cutouts.face"),
        ("{face: {outputs: [{suffix: ''}]}}", "cutouts.face.background"),
        ("{face: {background: none}}", "cutouts.face.outputs"),
        ("[1]", "cutouts"),
        ("{face: {background: none, outputs: [{suffix: '', box: [0, 0, 1024, 1], width: 256}]}}", "cutouts.face.outputs[0].width"),
        ("{face: {background: none, outputs: [{suffix: '_small'}]}}", "cutouts.face.outputs[0].suffix"),
        ("{face: {background: none, outputs: [{suffix: 'small'}]}}", "cutouts.face.outputs[0].suffix"),
        ("{face: {background: none, outputs: [{suffix: '-'}]}}", "cutouts.face.outputs[0].suffix"),
        ("{'../defaults': {background: none, outputs: [{suffix: ''}]}}", "cutouts.../defaults"),
        ("{face: {background: none, outputs: [{suffix: '', box: [5, 5, 1, 1]}]}}", "cutouts.face.outputs[0].box"),
    ],
)
def test_bad_cutouts_stop_with_location(repo, cutouts, where):
    with_cutouts(repo, f"cutouts: {cutouts}\n")
    with pytest.raises(ConfigError, match=re.escape(f"characters/c1/character.yaml: {where}")):
        load_character(repo, "c1")


def test_clear_colors_keep_optional_min_rg(repo):
    with_cutouts(
        repo,
        "cutouts:\n  face:\n    background: colors\n    clear_colors:\n"
        "      - {min: 200, max_rg: 10, max_gb: 10}\n"
        "      - {min: 150, max_rg: 40, max_gb: 30, min_rg: 5}\n"
        "    outputs: [{suffix: ''}]\n",
    )
    colors = load_character(repo, "c1").cutouts["face"].clear_colors
    assert colors == (ClearColor(200, 10, 10, None), ClearColor(150, 40, 30, 5))


def test_preview_background_is_optional(repo):
    assert load_preview_background(repo) is None
    write(repo, "defaults.yaml", 'style: color-anime\npreview_background: "#3366AA"\n')
    assert load_preview_background(repo) == "#3366AA"
    write(repo, "defaults.yaml", "style: color-anime\npreview_background: red\n")
    with pytest.raises(ConfigError, match=re.escape("defaults.yaml: preview_background")):
        load_preview_background(repo)


def test_preview_background_is_none_without_defaults_file(tmp_path):
    assert load_preview_background(tmp_path) is None
