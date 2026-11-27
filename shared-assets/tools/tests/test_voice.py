import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

import voice


class FakeEngine:
    """標準ライブラリだけの偽の VOICEVOX Engine。受けた要求を requests に残す。"""

    def __init__(self):
        self.requests: list[tuple[str, str, dict, bytes]] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _body(self):
                n = int(self.headers.get("Content-Length") or 0)
                return self.rfile.read(n) if n else b""

            def _send(self, data: bytes, ctype: str):
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                url = urlparse(self.path)
                outer.requests.append(("GET", url.path, parse_qs(url.query), b""))
                if url.path == "/version":
                    self._send(json.dumps("9.9.9").encode(), "application/json")
                elif url.path == "/speakers":
                    speakers = [{"name": "テスト話者", "styles": [{"id": 1, "name": "ノーマル"}, {"id": 2, "name": "あまあま"}]}]
                    self._send(json.dumps(speakers, ensure_ascii=False).encode(), "application/json")
                else:
                    self.send_error(404)

            def do_POST(self):
                url = urlparse(self.path)
                query = parse_qs(url.query)
                body = self._body()
                outer.requests.append(("POST", url.path, query, body))
                if url.path == "/audio_query":
                    text = query["text"][0]
                    # 本物の Engine のように、アクセント句ごとの mora と pitch を返す（"/" で句を区切り、1 文字 1 mora、pitch は 6.0）
                    phrases = [
                        {"moras": [{"text": ch, "pitch": 6.0} for ch in part]} for part in text.split("/") if part
                    ]
                    q = {"text": text, "speaker": query["speaker"][0], "accent_phrases": phrases}
                    self._send(json.dumps(q, ensure_ascii=False).encode(), "application/json")
                elif url.path == "/synthesis":
                    q = json.loads(body)
                    self._send(b"RIFFfakeWAVE" + q["text"].encode() + b"@" + query["speaker"][0].encode(), "audio/wav")
                else:
                    self.send_error(404)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def synth_requests(self):
        return [r for r in self.requests if r[1] in ("/audio_query", "/synthesis")]

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def engine():
    e = FakeEngine()
    yield e
    e.close()


@pytest.fixture
def items_path(tmp_path):
    items = {
        "categories": [{"key": "animal", "label": "どうぶつ"}],
        "items": [
            {"id": "dog", "category": "animal", "label": "いぬ", "kana": "いぬ", "reading": "いぬ"},
            {"id": "tomato", "category": "animal", "label": "トマト", "kana": "とまと", "reading": "トマト"},
        ],
    }
    path = tmp_path / "items.json"
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return path


def test_synthesize_calls_query_then_synthesis(engine):
    wav = voice.synthesize("ぞうさんは どれ？", 3, engine.url)
    posts = [r for r in engine.requests if r[0] == "POST"]
    assert [r[1] for r in posts] == ["/audio_query", "/synthesis"]
    assert posts[0][2]["text"] == ["ぞうさんは どれ？"] and posts[0][2]["speaker"] == ["3"]
    assert posts[1][2]["speaker"] == ["3"]
    assert wav == b"RIFFfakeWAVE" + "ぞうさんは どれ？".encode() + b"@3"


def test_build_writes_wav_and_manifest(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    written = voice.build(items_path, out, 1, engine.url)
    assert sorted(p.name for p in written) == ["dog.wav", "tomato.wav"]
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["speaker"] == 1
    assert manifest["speaker_name"] == "テスト話者"
    assert manifest["engine_version"] == "9.9.9"
    assert manifest["files"]["tomato"]["text"] == "トマト"
    assert len(manifest["files"]["dog"]["sha256"]) == 64


def test_build_skips_unchanged(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url)
    engine.requests.clear()
    voice.build(items_path, out, 1, engine.url)
    assert engine.synth_requests() == []


def test_build_redoes_when_speaker_changes(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url)
    engine.requests.clear()
    voice.build(items_path, out, 2, engine.url)
    assert len(engine.synth_requests()) == 4  # 2 つの声 × (audio_query と synthesis)
    assert json.loads((out / "manifest.json").read_text(encoding="utf-8"))["speaker"] == 2


def test_build_redoes_only_changed_text(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url)
    data = json.loads(items_path.read_text(encoding="utf-8"))
    data["items"][1]["reading"] = "とまと"
    items_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    engine.requests.clear()
    voice.build(items_path, out, 1, engine.url)
    assert len(engine.synth_requests()) == 2  # トマトの 1 つだけ


def test_build_redoes_when_wav_was_deleted(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url)
    (out / "dog.wav").unlink()
    engine.requests.clear()
    voice.build(items_path, out, 1, engine.url)
    assert len(engine.synth_requests()) == 2
    assert (out / "dog.wav").is_file()


def test_build_removes_voice_of_removed_item(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url)
    data = json.loads(items_path.read_text(encoding="utf-8"))
    data["items"] = data["items"][:1]
    items_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    voice.build(items_path, out, 1, engine.url)
    assert sorted(p.name for p in out.glob("*.wav")) == ["dog.wav"]
    assert list(json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]) == ["dog"]


def test_unknown_speaker_is_reported(engine, items_path, tmp_path):
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 99, engine.url)
    assert "99" in str(e.value)


def test_unreachable_engine_message(tmp_path, items_path):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # 閉じたポート
    with pytest.raises(voice.VoiceError) as e:
        voice.synthesize("いぬ", 1, f"http://127.0.0.1:{port}")
    assert "~/opt/voicevox_engine/run" in str(e.value)


# ---- 決まり文句（phrases.json） ----


def write_phrases(tmp_path, **override):
    data = {
        "templates": {"ask": "{reading}は どれ？", "ok": "そう、{reading}！"},
        "single": {"again": "もういっかい やる？"},
        "kana": {},
    }
    data.update(override)
    path = tmp_path / "phrases.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def phrases_path(tmp_path):
    return write_phrases(tmp_path)


def wavs(out):
    return sorted(p.name for p in out.glob("*.wav"))


def test_synthesize_with_kana_asks_the_engine_to_read_it_as_kana(engine):
    voice.synthesize("ゾ'ーワ/ド'レ?", 3, engine.url, is_kana=True)
    query = [r for r in engine.requests if r[1] == "/audio_query"][0][2]
    assert query["is_kana"] == ["true"]


def test_synthesize_without_kana_does_not_send_is_kana(engine):
    voice.synthesize("いぬ", 3, engine.url)
    query = [r for r in engine.requests if r[1] == "/audio_query"][0][2]
    assert "is_kana" not in query


def test_build_makes_phrase_voices(engine, items_path, phrases_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, phrases_path)
    assert wavs(out) == [
        "again.wav", "ask-dog.wav", "ask-tomato.wav", "dog.wav", "ok-dog.wav", "ok-tomato.wav", "tomato.wav",
    ]
    files = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]
    assert files["ask-dog"]["text"] == "いぬは どれ？"
    assert files["ask-tomato"]["text"] == "トマトは どれ？"
    assert files["ok-tomato"]["text"] == "そう、トマト！"
    assert files["again"]["text"] == "もういっかい やる？"
    assert files["dog"]["text"] == "いぬ"


def test_build_uses_the_kana_override_for_that_file_only(engine, items_path, tmp_path):
    phrases = write_phrases(tmp_path, kana={"ask-dog": "イ'ヌワ/ド'レ?"})
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, phrases)
    queries = [r[2] for r in engine.requests if r[1] == "/audio_query"]
    kana_queries = [q for q in queries if q.get("is_kana") == ["true"]]
    assert [q["text"][0] for q in kana_queries] == ["イ'ヌワ/ド'レ?"]
    files = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]
    assert files["ask-dog"]["text"] == "イ'ヌワ/ド'レ?"
    assert files["ask-tomato"]["text"] == "トマトは どれ？"


def test_build_skips_unchanged_phrases(engine, items_path, phrases_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, phrases_path)
    engine.requests.clear()
    voice.build(items_path, out, 1, engine.url, phrases_path)
    assert engine.synth_requests() == []


def test_build_redoes_only_the_file_whose_kana_was_added(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, write_phrases(tmp_path))
    engine.requests.clear()
    voice.build(items_path, out, 1, engine.url, write_phrases(tmp_path, kana={"ask-dog": "イ'ヌワ/ド'レ?"}))
    assert len(engine.synth_requests()) == 2  # ask-dog の 1 つだけ（audio_query と synthesis）


def test_build_removes_the_voice_of_a_removed_phrase_but_not_item_voices(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, write_phrases(tmp_path))
    voice.build(items_path, out, 1, engine.url, write_phrases(tmp_path, single={}))
    assert "again.wav" not in wavs(out)
    assert {"dog.wav", "tomato.wav", "ask-dog.wav"} <= set(wavs(out))
    assert "again" not in json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]


def test_build_without_phrases_makes_only_item_voices(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url)
    assert wavs(out) == ["dog.wav", "tomato.wav"]


@pytest.mark.parametrize(
    "override, word",
    [
        ({"templates": None}, "templates"),
        ({"templates": {"ask": "どれ？"}}, "ask"),
        ({"templates": {"ask": "{reading}は どれ？"}, "single": {"ask": "あ"}}, "ask"),
        ({"kana": {"ask-nothing": "ア"}}, "ask-nothing"),
        ({"single": {"again": ""}}, "again"),
    ],
)
def test_bad_phrases_name_the_broken_entry(engine, items_path, tmp_path, override, word):
    data = {"templates": {"ask": "{reading}は どれ？"}, "single": {"again": "もういっかい"}, "kana": {}}
    for key, value in override.items():
        if value is None:
            data.pop(key)
        else:
            data[key] = value
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, path)
    assert word in str(e.value)


def test_duplicate_key_in_phrases_json_is_reported(engine, items_path, tmp_path):
    path = tmp_path / "dup.json"
    path.write_text('{"templates": {"ask": "{reading}", "ask": "{reading}は"}, "single": {}}', encoding="utf-8")
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, path)
    assert "ask" in str(e.value)


# ---- 抑揚（contour）: 決まり文句のアクセント句の pitch を、名前の部分の高さを基準に決める ----


def query_of(*phrases):
    return {"accent_phrases": [{"moras": [{"text": "あ", "pitch": p} for p in ps]} for ps in phrases]}


def pitches(q, i):
    return [round(m["pitch"], 3) for m in q["accent_phrases"][i]["moras"]]


def test_apply_contour_sets_the_phrase_around_the_base_of_the_other_phrases():
    q = query_of([5.8, 6.0, 0.0], [6.2, 6.2])  # 基準は、他の句の声のある mora（pitch > 0）の平均 = 5.9
    voice.apply_contour(q, {"phrase": -1, "offsets": [-0.1, 0.1]})
    assert pitches(q, 1) == [5.8, 6.0]
    assert pitches(q, 0) == [5.8, 6.0, 0.0]  # 他の句は触らない


def test_apply_contour_on_the_first_phrase():
    q = query_of([5.0, 5.0], [6.2, 6.4])  # 基準 = 6.3
    voice.apply_contour(q, {"phrase": 0, "offsets": [0.12, -0.12]})
    assert pitches(q, 0) == [6.42, 6.18]
    assert pitches(q, 1) == [6.2, 6.4]


def test_apply_contour_rejects_a_wrong_number_of_offsets():
    with pytest.raises(voice.VoiceError) as e:
        voice.apply_contour(query_of([6.0, 6.0, 6.0], [6.0, 6.0]), {"phrase": -1, "offsets": [0.0]})
    assert "offsets" in str(e.value)


def test_apply_contour_rejects_a_missing_phrase():
    with pytest.raises(voice.VoiceError) as e:
        voice.apply_contour(query_of([6.0]), {"phrase": 3, "offsets": [0.0]})
    assert "phrase" in str(e.value)


def contour_phrases(tmp_path, offsets=(-0.1, 0.0)):
    return write_phrases(
        tmp_path,
        single={},
        templates={"ask": "{reading}は どれ？"},
        kana={"ask-dog": "イヌワ/ドレ", "ask-tomato": "トマトワ/ドレ"},
        contour={"ask": {"phrase": -1, "offsets": list(offsets)}},
    )


def synthesis_pitches(engine, text):
    for _, path, _, body in engine.requests:
        if path == "/synthesis" and json.loads(body)["text"] == text:
            return pitches(json.loads(body), -1)
    raise AssertionError(f"{text} の合成の要求が無い")


def test_build_applies_the_contour_before_synthesis(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, contour_phrases(tmp_path))
    assert synthesis_pitches(engine, "イヌワ/ドレ") == [5.9, 6.0]
    files = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]
    assert files["ask-dog"]["contour"] == {"phrase": -1, "offsets": [-0.1, 0.0]}
    assert "contour" not in files["dog"]


def test_build_redoes_only_the_files_whose_contour_changed(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, contour_phrases(tmp_path))
    engine.requests.clear()
    voice.build(items_path, out, 1, engine.url, contour_phrases(tmp_path))
    assert engine.synth_requests() == []
    voice.build(items_path, out, 1, engine.url, contour_phrases(tmp_path, offsets=(-0.2, 0.0)))
    assert len(engine.synth_requests()) == 4  # ask-dog と ask-tomato（audio_query と synthesis）
    assert synthesis_pitches(engine, "イヌワ/ドレ") == [5.8, 6.0]


def test_a_contour_that_does_not_fit_names_the_file(engine, items_path, tmp_path):
    bad = write_phrases(tmp_path, kana={}, contour={"ok": {"phrase": -1, "offsets": [0.0, 0.0]}})
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, bad)
    assert "ok-dog" in str(e.value)


def test_a_contour_for_an_unknown_phrase_is_reported(engine, items_path, tmp_path):
    bad = write_phrases(tmp_path, contour={"nope": {"phrase": 0, "offsets": [0.0]}})
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, bad)
    assert "nope" in str(e.value)


def test_text_override_replaces_the_sentence_for_that_file_only(engine, items_path, tmp_path):
    phrases = write_phrases(tmp_path, text={"ask-dog": "イヌは どれ？"})
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, phrases)
    files = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]
    assert files["ask-dog"]["text"] == "イヌは どれ？"
    assert "kana" not in files["ask-dog"]  # 普通の文として Engine に渡す
    assert files["ask-tomato"]["text"] == "トマトは どれ？"
    queries = [r[2] for r in engine.requests if r[1] == "/audio_query"]
    assert not any(q.get("is_kana") for q in queries)


def test_kana_wins_over_text(engine, items_path, tmp_path):
    phrases = write_phrases(tmp_path, text={"ask-dog": "イヌは どれ？"}, kana={"ask-dog": "イヌワ'/ドレ？"})
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, phrases)
    files = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]
    assert files["ask-dog"]["text"] == "イヌワ'/ドレ？" and files["ask-dog"]["kana"] is True


def test_text_override_for_an_unknown_file_is_reported(engine, items_path, tmp_path):
    bad = write_phrases(tmp_path, text={"ask-nothing": "あ"})
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, bad)
    assert "ask-nothing" in str(e.value)


# ---- ？の上がり（rise）: 最後の mora を伸ばした音を足し、基準 + offset の高さにする ----


def rise_contour(offset=0.1, seconds=0.15):
    return {"phrase": -1, "offsets": [0.2, 0.0], "rise": {"offset": offset, "seconds": seconds}}


def test_apply_contour_adds_a_rising_mora_after_the_last_one():
    q = query_of([5.8, 5.8], [6.5, 6.5])
    q["accent_phrases"][1]["is_interrogative"] = True
    q["accent_phrases"][1]["moras"][-1].update({"text": "レ", "consonant": "r", "vowel": "e", "vowel_length": 0.3})
    assert voice.apply_contour(q, rise_contour()) is True
    moras = q["accent_phrases"][1]["moras"]
    assert [round(m["pitch"], 3) for m in moras] == [6.0, 5.8, 5.9]
    assert moras[-1]["vowel"] == "e" and moras[-1]["consonant"] is None
    assert moras[-1]["vowel_length"] == 0.15
    assert q["accent_phrases"][1]["is_interrogative"] is False  # Engine の自動の上がりと二重にしない


def test_apply_contour_without_rise_leaves_the_interrogative_alone():
    q = query_of([5.8], [6.5, 6.5])
    q["accent_phrases"][1]["is_interrogative"] = True
    assert voice.apply_contour(q, {"phrase": -1, "offsets": [0.1, 0.0]}) is False
    assert len(q["accent_phrases"][1]["moras"]) == 2
    assert q["accent_phrases"][1]["is_interrogative"] is True


def test_synthesize_turns_off_the_engine_upspeak_when_the_contour_has_a_rise(engine):
    voice.synthesize("イヌワ/ドレ", 1, engine.url, False, rise_contour())
    synthesis = [r for r in engine.requests if r[1] == "/synthesis"][0]
    assert synthesis[2]["enable_interrogative_upspeak"] == ["false"]
    plain = engine.requests.copy()
    engine.requests.clear()
    voice.synthesize("イヌワ/ドレ", 1, engine.url, False, {"phrase": -1, "offsets": [0.1, 0.0]})
    synthesis = [r for r in engine.requests if r[1] == "/synthesis"][0]
    assert "enable_interrogative_upspeak" not in synthesis[2]
    assert plain


@pytest.mark.parametrize(
    "rise",
    [{"offset": 0.1}, {"seconds": 0.1}, {"offset": "x", "seconds": 0.1}, {"offset": 0.1, "seconds": 0}, 3],
)
def test_a_broken_rise_names_the_entry(engine, items_path, tmp_path, rise):
    bad = write_phrases(
        tmp_path, kana={}, contour={"ask": {"phrase": -1, "offsets": [0.0], "rise": rise}}
    )
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, bad)
    assert "contour.ask" in str(e.value) and "rise" in str(e.value)


# ---- 名前の高さ（name_contour）: 決まり文句の中の名前の、頭の数 mora を、決まった高さにする ----


def name_step(base=6.0, offsets=(-0.2, 0.0)):
    return {"base": base, "offsets": list(offsets)}


def test_apply_contour_sets_the_first_moras_of_the_name_phrase_after_the_template_part():
    q = query_of([5.9, 5.7, 5.6], [6.5, 6.5])
    contour = {"phrase": -1, "offsets": [0.2, 0.0], "name_phrase": 0, "name": name_step()}
    voice.apply_contour(q, contour)
    # 決まり文句の部分の基準は、直す前の名前の高さの平均（5.9 + 5.7 + 5.6）/ 3
    assert pitches(q, 1) == [5.933, 5.733]
    # 名前は、基準 6.0 に offsets を足す（3 つ目の mora は触らない）
    assert pitches(q, 0) == [5.8, 6.0, 5.6]


def test_apply_contour_rejects_a_name_with_fewer_moras_than_offsets():
    contour = {"phrase": -1, "offsets": [0.0, 0.0], "name_phrase": 0, "name": name_step(offsets=(0.0, 0.0, 0.0))}
    with pytest.raises(voice.VoiceError) as e:
        voice.apply_contour(query_of([5.9, 5.7], [6.5, 6.5]), contour)
    assert "name" in str(e.value)


def name_phrases(tmp_path, name_contour):
    return write_phrases(
        tmp_path,
        single={},
        templates={"ask": "{reading}は どれ？"},
        kana={"ask-dog": "イヌワ/ドレ", "ask-tomato": "トマトワ/ドレ"},
        contour={"ask": {"phrase": -1, "offsets": [-0.1, 0.0], "name_phrase": 0}},
        name_contour=name_contour,
    )


def synthesis_phrase_pitches(engine, text, index):
    for _, path, _, body in engine.requests:
        if path == "/synthesis" and json.loads(body)["text"] == text:
            return pitches(json.loads(body), index)
    raise AssertionError(f"{text} の合成の要求が無い")


def test_build_applies_the_name_contour_to_that_item_only(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, name_phrases(tmp_path, {"dog": name_step(offsets=(-0.3, 0.0))}))
    assert synthesis_phrase_pitches(engine, "イヌワ/ドレ", 0) == [5.7, 6.0, 6.0]
    assert synthesis_phrase_pitches(engine, "トマトワ/ドレ", 0) == [6.0, 6.0, 6.0, 6.0]
    files = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]
    assert files["ask-dog"]["contour"]["name"] == name_step(offsets=(-0.3, 0.0))
    assert "name" not in files["ask-tomato"]["contour"]


def test_changing_a_name_contour_redoes_only_that_items_voices(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, name_phrases(tmp_path, {"dog": name_step()}))
    engine.requests.clear()
    voice.build(items_path, out, 1, engine.url, name_phrases(tmp_path, {"dog": name_step(offsets=(-0.4, 0.0))}))
    assert len(engine.synth_requests()) == 4  # dog（名前の声）と ask-dog の 2 つ（audio_query と synthesis）


def test_a_name_contour_for_an_unknown_item_is_reported(engine, items_path, tmp_path):
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, name_phrases(tmp_path, {"cow": name_step()}))
    assert "name_contour.cow" in str(e.value)


def test_a_name_contour_needs_name_phrase_in_the_template_contour(engine, items_path, tmp_path):
    phrases = write_phrases(
        tmp_path,
        kana={"ask-dog": "イヌワ/ドレ", "ask-tomato": "トマトワ/ドレ"},
        single={},
        templates={"ask": "{reading}は どれ？"},
        contour={"ask": {"phrase": -1, "offsets": [-0.1, 0.0]}},
        name_contour={"dog": name_step()},
    )
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, phrases)
    assert "name_phrase" in str(e.value)


@pytest.mark.parametrize("step", [{"offsets": [0.0]}, {"base": 6.0}, {"base": 6.0, "offsets": []}, {"base": "x", "offsets": [0.0]}, 3])
def test_a_broken_name_contour_names_the_entry(engine, items_path, tmp_path, step):
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, name_phrases(tmp_path, {"dog": step}))
    assert "name_contour.dog" in str(e.value)


# ---- 名前の声そのもの（<id>.wav）にも name_contour を効かせる ----


def test_apply_contour_uses_the_given_base_instead_of_the_computed_one():
    q = query_of([5.0, 5.0])
    voice.apply_contour(q, {"phrase": 0, "offsets": [-0.3, 0.0], "base": 6.0})
    assert pitches(q, 0) == [5.7, 6.0]


def test_build_applies_the_name_contour_to_the_name_voice_too(engine, items_path, tmp_path):
    out = tmp_path / "voice"
    voice.build(items_path, out, 1, engine.url, name_phrases(tmp_path, {"dog": name_step(offsets=(-0.3, 0.0))}))
    assert synthesis_phrase_pitches(engine, "いぬ", 0) == [5.7, 6.0]
    assert synthesis_phrase_pitches(engine, "トマト", 0) == [6.0, 6.0, 6.0]
    files = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]
    assert files["dog"]["contour"] == {"phrase": 0, "offsets": [-0.3, 0.0], "base": 6.0}
    assert "contour" not in files["tomato"]


def test_a_name_contour_that_does_not_fit_the_name_voice_names_the_item(engine, items_path, tmp_path):
    bad = name_phrases(tmp_path, {"dog": name_step(offsets=(0.0, 0.0, 0.0))})
    with pytest.raises(voice.VoiceError) as e:
        voice.build(items_path, tmp_path / "voice", 1, engine.url, bad)
    assert "dog" in str(e.value)
