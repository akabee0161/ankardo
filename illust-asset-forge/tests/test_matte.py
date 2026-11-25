import io
import json

import pytest
from PIL import Image

from artgen.export import ExportError
from artgen.matte import MODEL_SHA256, load_matte_with_sha, save_mattes
from test_export import put, repo  # noqa: F401


@pytest.fixture
def cropped_repo(repo):
    put(repo, "face.png", (1024, 1024), "face")
    return repo


def png_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_save_and_load_roundtrip(cropped_repo):
    mask = Image.new("L", (1024, 1024), 200)
    save_mattes(cropped_repo, "c1", {"face.png": png_bytes(mask)}, MODEL_SHA256)
    assert (cropped_repo / "characters/c1/matte/face.png").is_file()
    record = json.loads((cropped_repo / "characters/c1/matte/matte.json").read_text(encoding="utf-8"))
    assert record["model_sha256"] == MODEL_SHA256 and list(record["sources"]) == ["face.png"]
    loaded, sha = load_matte_with_sha(cropped_repo, "c1", "face.png")
    assert len(sha) == 64
    assert loaded.mode == "L" and loaded.size == (1024, 1024) and loaded.getpixel((5, 5)) == 200


def test_load_missing_matte_stops(cropped_repo):
    with pytest.raises(ExportError, match="cloud matte c1"):
        load_matte_with_sha(cropped_repo, "c1", "face.png")


def test_load_stale_matte_stops(cropped_repo):
    save_mattes(cropped_repo, "c1", {"face.png": png_bytes(Image.new("L", (1024, 1024), 255))}, MODEL_SHA256)
    put(cropped_repo, "face.png", (1024, 1024), "face", seed=99)  # 元画像を入れ替えた
    with pytest.raises(ExportError, match="古い"):
        load_matte_with_sha(cropped_repo, "c1", "face.png")


def test_save_rejects_other_model(cropped_repo):
    with pytest.raises(ExportError, match="モデル"):
        save_mattes(cropped_repo, "c1", {"face.png": png_bytes(Image.new("L", (1024, 1024)))}, "0" * 64)


def test_save_rejects_mask_of_wrong_size(cropped_repo):
    with pytest.raises(ExportError, match="大きさ"):
        save_mattes(cropped_repo, "c1", {"face.png": png_bytes(Image.new("L", (512, 512)))}, MODEL_SHA256)
    assert not (cropped_repo / "characters/c1/matte").exists()


def test_harden_makes_unsure_background_transparent_and_keeps_a_soft_edge():
    from artgen.matte import harden

    mask = Image.new("L", (5, 1))
    for x, v in enumerate([60, 128, 164, 200, 250]):
        mask.putpixel((x, 0), v)
    out = harden(mask)
    assert [out.getpixel((x, 0)) for x in range(5)] == [0, 0, 128, 255, 255]


def _candidate(tmp_path, name="c1_face_1.png"):
    p = tmp_path / "local/runs/c1/face/r/" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), (200, 200, 200)).save(p)
    return p


def test_candidate_mattes_are_cached_next_to_the_candidate(tmp_path):
    from artgen.matte import candidate_matte_path, ensure_candidate_mattes

    a, b = _candidate(tmp_path), _candidate(tmp_path, "c1_face_2.png")
    calls = []

    def run(images):
        calls.append(sorted(images))
        return MODEL_SHA256, {k: png_bytes(Image.new("L", (64, 64), 255)) for k in images}

    ensure_candidate_mattes([a, b], run)
    assert candidate_matte_path(a).is_file() and candidate_matte_path(b).is_file()
    ensure_candidate_mattes([a, b], run)  # 2 回目は Modal を呼ばない
    assert len(calls) == 1 and len(calls[0]) == 2


def test_candidate_mattes_from_other_model_are_not_saved(tmp_path):
    from artgen.matte import candidate_matte_path, ensure_candidate_mattes

    a = _candidate(tmp_path)
    with pytest.raises(ExportError, match="モデル"):
        ensure_candidate_mattes([a], lambda images: ("0" * 64, {k: b"" for k in images}))
    assert not candidate_matte_path(a).exists()


def test_candidate_mattes_are_sent_in_batches_and_saved_per_batch(tmp_path, monkeypatch):
    import artgen.matte as M
    from artgen.matte import candidate_matte_path, ensure_candidate_mattes

    monkeypatch.setattr(M, "CANDIDATE_BATCH", 2)
    paths = [_candidate(tmp_path, f"c1_face_{i}.png") for i in range(5)]
    sizes = []

    def run(images):
        sizes.append(len(images))
        if len(sizes) == 3:
            raise RuntimeError("Modal が落ちた")
        return MODEL_SHA256, {k: png_bytes(Image.new("L", (64, 64), 255)) for k in images}

    with pytest.raises(RuntimeError):
        ensure_candidate_mattes(paths, run)
    assert sizes == [2, 2, 1]
    assert [candidate_matte_path(p).is_file() for p in paths] == [True, True, True, True, False]


def test_save_rejects_mask_when_source_changed_after_sending(cropped_repo):
    sent = (cropped_repo / "characters/c1/source/face.png").read_bytes()
    put(cropped_repo, "face.png", (1024, 1024), "face", seed=99)  # 送ったあとで差し替えた
    with pytest.raises(ExportError, match="差し替"):
        save_mattes(cropped_repo, "c1", {"face.png": png_bytes(Image.new("L", (1024, 1024)))}, MODEL_SHA256,
                    sent={"face.png": sent})
    assert not (cropped_repo / "characters/c1/matte").exists()


def test_load_with_non_dict_matte_json_stops(cropped_repo):
    save_mattes(cropped_repo, "c1", {"face.png": png_bytes(Image.new("L", (1024, 1024), 255))}, MODEL_SHA256)
    (cropped_repo / "characters/c1/matte/matte.json").write_text("[1]", encoding="utf-8")
    with pytest.raises(ExportError, match="matte.json"):
        load_matte_with_sha(cropped_repo, "c1", "face.png")


def test_candidate_matte_is_not_left_half_written(tmp_path, monkeypatch):
    import os

    from artgen.matte import candidate_matte_path, ensure_candidate_mattes

    a = _candidate(tmp_path)

    def broken_replace(src, dst):
        raise OSError("書き込み中に落ちた")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(OSError):
        ensure_candidate_mattes([a], lambda images: (MODEL_SHA256, {k: png_bytes(Image.new("L", (64, 64), 255)) for k in images}))
    assert not candidate_matte_path(a).exists()
    assert not list(a.parent.glob("*.tmp"))


def test_candidate_mattes_stop_when_modal_returns_too_few(tmp_path):
    from artgen.matte import candidate_matte_path, ensure_candidate_mattes

    a, b = _candidate(tmp_path), _candidate(tmp_path, "c1_face_2.png")
    with pytest.raises(ExportError, match="足りない"):
        ensure_candidate_mattes([a, b], lambda images: (MODEL_SHA256, {"0": png_bytes(Image.new("L", (64, 64), 255))}))
    assert not candidate_matte_path(a).exists() and not candidate_matte_path(b).exists()


def test_load_compares_with_given_source_sha_instead_of_the_file(cropped_repo):
    import hashlib

    src = cropped_repo / "characters/c1/source/face.png"
    original = hashlib.sha256(src.read_bytes()).hexdigest()
    save_mattes(cropped_repo, "c1", {"face.png": png_bytes(Image.new("L", (1024, 1024), 255))}, MODEL_SHA256)
    put(cropped_repo, "face.png", (1024, 1024), "face", seed=99)  # 読んだ後にファイルが差し替わった
    load_matte_with_sha(cropped_repo, "c1", "face.png", source_sha=original)  # 読んだ bytes と照合するので通る
    with pytest.raises(ExportError, match="古い"):
        load_matte_with_sha(cropped_repo, "c1", "face.png", source_sha="0" * 64)
