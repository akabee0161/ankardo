import json
import wave
from pathlib import Path

CHIIKU = Path(__file__).resolve().parents[2] / "chiiku"

ANIMALS = ["dog", "cat", "cow", "pig", "chicken", "elephant"]
MAX_CRY_SECONDS = 3.0


def items():
    return json.loads((CHIIKU / "items.json").read_text(encoding="utf-8"))["items"]


def test_animals_in_items_are_the_six_with_cries():
    assert [i["id"] for i in items() if i["category"] == "animal"] == ANIMALS


def test_every_animal_has_cry():
    # 形式は wav。ffmpeg が無く ogg を mp3 にできないうえ、ogg は古い iOS で鳴らないため
    for item in items():
        if item["category"] != "animal":
            continue
        path = CHIIKU / "cry" / f"{item['id']}.wav"
        assert path.is_file(), f"{path.name} が無い"
        with wave.open(str(path)) as w:
            seconds = w.getnframes() / w.getframerate()
            assert 0.3 <= seconds <= MAX_CRY_SECONDS, f"{path.name} が {seconds:.2f} 秒"


def test_only_animals_have_cries():
    ids = {i["id"] for i in items() if i["category"] == "animal"}
    assert {p.stem for p in (CHIIKU / "cry").glob("*.wav")} == ids


def test_credits_list_every_cry_and_voice():
    text = (CHIIKU / "CREDITS.md").read_text(encoding="utf-8")
    manifest = json.loads((CHIIKU / "voice" / "manifest.json").read_text(encoding="utf-8"))
    assert f"VOICEVOX:{manifest['speaker_name']}" in text
    sections = text.split("\n### ")[1:]
    for animal in ANIMALS:
        block = next((s for s in sections if s.startswith(animal)), None)
        assert block is not None, f"{animal} の節が CREDITS.md に無い"
        assert "出典: https://" in block, animal
        assert "規約:" in block, animal
        assert "クレジット:" in block, animal
