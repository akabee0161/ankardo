from pathlib import Path

import pytest

from artgen.config import load_character, load_template
from artgen.prompt import build_prompt
from artgen.config import load_style

ROOT = Path(__file__).resolve().parent.parent

# 2026-11-25 に依頼者が絵を見て入れ替えた（かぶとむし→とんぼ、さめ→いるか、おにぎり→パン・スパゲッティ）
OBJECT_IDS = [
    "dog", "cat", "cow", "pig", "chicken", "elephant",
    "butterfly", "ladybug", "dragonfly",
    "goldfish", "pufferfish", "dolphin",
    "tomato", "carrot", "eggplant", "corn",
    "apple", "banana", "strawberry", "bread", "spaghetti",
]
SAMPLE_IDS = ["knight", "mage", "schoolboy", "schoolgirl"]


def _prompt(char_id):
    character = load_character(ROOT, char_id)
    template = load_template(ROOT, "object")
    return build_prompt(load_style(ROOT, character.style), template, character)


@pytest.mark.parametrize("char_id", OBJECT_IDS)
def test_all_twenty_load(char_id):
    assert _prompt(char_id).positive


def test_ids_are_distinct():
    assert len(set(OBJECT_IDS)) == len(OBJECT_IDS) == 21


@pytest.mark.parametrize("char_id", OBJECT_IDS)
def test_prompt_has_no_humans(char_id):
    assert "no humans" in _prompt(char_id).positive


@pytest.mark.parametrize("char_id", OBJECT_IDS)
def test_every_object_has_cutout(char_id):
    cutout = load_character(ROOT, char_id).cutouts["object"]
    # 17 種類は matte。背景除去モデルが全面透明にした 4 種類（ladybug・tomato・carrot・apple）だけ colors
    assert cutout.background in ("matte", "colors")
    if cutout.background == "colors":
        assert cutout.clear_colors, "colors のときは背景色の条件（clear_colors）が要る。無いと白以外の背景が消えない"
    assert len(cutout.outputs) == 1 and cutout.outputs[0].width == 512


def test_no_extra_characters_named_like_objects():
    ids = sorted(p.name for p in (ROOT / "characters").iterdir() if p.is_dir())
    assert ids == sorted(OBJECT_IDS + SAMPLE_IDS)
