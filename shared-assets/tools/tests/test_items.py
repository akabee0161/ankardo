import json
import re
from pathlib import Path

ITEMS_PATH = Path(__file__).resolve().parents[2] / "chiiku" / "items.json"

# 設計書 3.1 の並びを、2026-11-25 の入れ替え（かぶとむし→とんぼ、さめ→いるか、おにぎり→パン・スパゲッティ）に合わせたもの
EXPECTED_IDS = [
    "dog", "cat", "cow", "pig", "chicken", "elephant",
    "butterfly", "ladybug", "dragonfly",
    "goldfish", "pufferfish", "dolphin",
    "tomato", "carrot", "eggplant", "corn",
    "apple", "banana", "strawberry", "bread", "spaghetti",
]


def load():
    return json.loads(ITEMS_PATH.read_text(encoding="utf-8"))


def test_twenty_one_items_in_spec_order():
    items = load()["items"]
    assert [i["id"] for i in items] == EXPECTED_IDS
    counts = [sum(1 for i in items if i["category"] == c["key"]) for c in load()["categories"]]
    assert counts == [6, 3, 3, 4, 5]


def test_kana_is_hiragana():
    for item in load()["items"]:
        assert re.fullmatch(r"[ぁ-ゖー]+", item["kana"]), item


def test_categories_match():
    data = load()
    keys = [c["key"] for c in data["categories"]]
    assert keys == ["animal", "insect", "sea", "vegetable", "food"]
    assert all(i["category"] in keys for i in data["items"])


def test_every_item_has_all_fields():
    for item in load()["items"]:
        assert set(item) == {"id", "category", "label", "kana", "reading"}, item
        assert all(isinstance(v, str) and v for v in item.values()), item
