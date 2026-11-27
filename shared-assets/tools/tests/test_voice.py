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
                    q = {"text": query["text"][0], "speaker": query["speaker"][0]}
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
