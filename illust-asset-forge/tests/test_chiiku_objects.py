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
def test_all_load(char_id):
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


@pytest.mark.parametrize("char_id", OBJECT_IDS)
def test_every_object_is_cropped_to_a_square_inside_the_source(char_id):
    # 絵の大きさをそろえる方針: 絵の長い辺が枠の約 90% になる正方形で、元の絵（1024）から切り出す。
    # box が null（全体）だと、てんとうむし 8%・ぞう 71% のように、枠に占める大きさがばらつく
    box = load_character(ROOT, char_id).cutouts["object"].outputs[0].box
    assert box is not None, "box が無い（元の絵の全体を縮めると、絵の大きさがそろわない）"
    x0, y0, x1, y1 = box
    assert x1 - x0 == y1 - y0, f"正方形でない: {box}"
    assert 0 <= x0 < x1 <= 1024 and 0 <= y0 < y1 <= 1024, f"元の絵（1024）の外にはみ出す: {box}"
