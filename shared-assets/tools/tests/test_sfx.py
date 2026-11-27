import io
import struct
import wave

import pytest

import sfx

NAMES = ["correct", "wrong"]


def read(name: str):
    with wave.open(io.BytesIO(sfx.render(name))) as w:
        params = (w.getnchannels(), w.getsampwidth(), w.getframerate())
        frames = w.readframes(w.getnframes())
        samples = struct.unpack(f"<{w.getnframes()}h", frames)
        return params, samples, w.getnframes() / w.getframerate()


@pytest.mark.parametrize("name", NAMES)
def test_format_is_16bit_mono_22050(name):
    params, _, _ = read(name)
    assert params == (1, 2, 22050)


@pytest.mark.parametrize("name", NAMES)
def test_length_is_short(name):
    _, _, seconds = read(name)
    assert 0.2 <= seconds <= 0.5


@pytest.mark.parametrize("name", NAMES)
def test_is_audible_but_gentle(name):
    _, samples, _ = read(name)
    peak = max(abs(s) for s in samples)
    assert 1000 < peak <= 32767 * 0.5


@pytest.mark.parametrize("name", NAMES)
def test_starts_and_ends_near_zero_so_it_does_not_click(name):
    _, samples, _ = read(name)
    assert abs(samples[0]) < 200
    assert abs(samples[-1]) < 200


@pytest.mark.parametrize("name", NAMES)
def test_same_bytes_every_time(name):
    assert sfx.render(name) == sfx.render(name)


def test_unknown_name_is_rejected():
    with pytest.raises(ValueError):
        sfx.render("nope")


def test_main_writes_both_files(tmp_path):
    assert sfx.main(["--out", str(tmp_path)]) == 0
    assert sorted(p.name for p in tmp_path.glob("*.wav")) == ["correct.wav", "wrong.wav"]
    assert (tmp_path / "correct.wav").read_bytes() == sfx.render("correct")
