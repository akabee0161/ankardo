import re
from pathlib import Path

import pytest
import yaml

from artgen.config import load_character, load_default_style, load_style, load_template
from artgen.mask import check_box, check_feather
from artgen.prompt import build_prompt

ROOT = Path(__file__).resolve().parent.parent
CHARACTER_IDS = sorted(p.parent.name for p in (ROOT / "characters").glob("*/character.yaml"))


def test_there_is_at_least_one_character():
    assert CHARACTER_IDS


@pytest.mark.parametrize("char_id", CHARACTER_IDS)
def test_all_characters_build_for_every_template_and_expression(char_id):
    character = load_character(ROOT, char_id)
    style = load_style(ROOT, character.style)
    for template_name in ("face", "fullbody"):
        template = load_template(ROOT, template_name)
        for expression in character.expressions:
            prompt = build_prompt(style, template, character, expression=expression)
            assert prompt.positive
            assert prompt.negative


def test_face_template_matches_spec():
    face = load_template(ROOT, "face")
    assert (face.width, face.height) == (1024, 1024)
    assert face.export_size == 256
    assert face.inpaint_strength is not None and face.inpaint_feather is not None
    fullbody = load_template(ROOT, "fullbody")
    assert (fullbody.width, fullbody.height) == (832, 1216)
    assert fullbody.export_size is None
    assert fullbody.use_items is True


def test_repo_does_not_mention_the_game():
    forbidden = ("character-tactics", "face_px", "18222c")
    skip_dirs = {".git", ".venv", ".superpowers", "docs", "tests", "__pycache__"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or skip_dirs & set(path.relative_to(ROOT).parts):
            continue
        if path.suffix in {".png", ".pyc"} or path.parent.name.endswith(".egg-info"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for word in forbidden:
            assert word not in text.lower(), f"{path.relative_to(ROOT)} に {word} がある"


def test_face_template_is_left_facing_upper_body_with_default_box():
    face = load_template(ROOT, "face")
    assert "upper body" in face.prompt
    assert "portrait" not in face.prompt
    assert "upper body" not in face.negative
    assert "looking to the side" in face.prompt
    assert face.inpaint_box is not None
    check_box(face.inpaint_box, (face.width, face.height))
    check_feather(face.inpaint_box, face.inpaint_feather)


def test_default_style_exists():
    assert load_default_style(ROOT) == "thick-line-flat"
    load_style(ROOT, load_default_style(ROOT))


@pytest.mark.parametrize("char_id", CHARACTER_IDS)
def test_characters_follow_default_style(char_id):
    data = yaml.safe_load((ROOT / "characters" / char_id / "character.yaml").read_text(encoding="utf-8"))
    assert "style" not in data


def test_style_candidates_exist():
    names = sorted(p.stem for p in (ROOT / "styles").glob("*.yaml"))
    assert names == ["color-anime", "retro-anime", "soft-cel", "soft-painterly", "thick-line-flat", "watercolor"]
    for name in names:
        load_style(ROOT, name)


def test_sample_characters_are_the_four_generic_ones():
    assert CHARACTER_IDS == ["knight", "mage", "schoolboy", "schoolgirl"]


def test_no_game_ids_or_trial_style_names():
    assert not [c for c in CHARACTER_IDS if re.fullmatch(r"ally\d+", c)]
    styles = sorted(p.stem for p in (ROOT / "styles").glob("*.yaml"))
    assert not [s for s in styles if s.startswith("tlf-")]


SAMPLE_IDS = ["knight", "mage", "schoolboy", "schoolgirl"]


@pytest.mark.parametrize("char_id", SAMPLE_IDS)  # 見本だけ。コピーした先で足す作品のキャラクターには当てはめない
def test_samples_have_no_style_or_inpaint_box(char_id):
    data = yaml.safe_load((ROOT / "characters" / char_id / "character.yaml").read_text(encoding="utf-8"))
    assert "style" not in data and "inpaint_box" not in data
    assert set(data["expressions"]) == {"normal", "hurt", "shout"}
