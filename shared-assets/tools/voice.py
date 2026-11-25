"""VOICEVOX Engine で、共通素材の名前の声（voice/<id>.wav）を作る。

Engine の起動:  ~/opt/voicevox_engine/run --host 127.0.0.1
使い方（ankardo のルートで）:
    python shared-assets/tools/voice.py --list-speakers
    python shared-assets/tools/voice.py --trial --speakers 3 8 --out local/voice-trial
    python shared-assets/tools/voice.py --speaker 3

接続先は環境変数 VOICEVOX_URL（既定 http://127.0.0.1:50021）。
text・speaker・Engine の版が前回と同じ声は作り直さない。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ITEMS = ROOT / "shared-assets" / "chiiku" / "items.json"
DEFAULT_OUT = ROOT / "shared-assets" / "chiiku" / "voice"
DEFAULT_URL = "http://127.0.0.1:50021"
TIMEOUT = 60

TRIAL_TEXTS = {"inu": "いぬ", "toumorokoshi": "とうもろこし", "elephant-q": "ぞうさんは どれ？"}

START_HINT = "VOICEVOX Engine を起動する（~/opt/voicevox_engine/run --host 127.0.0.1）"


class VoiceError(Exception):
    """声を作れない（Engine に繋がらない・話者が無い・応答が不正）。"""


def _request(method: str, base_url: str, path: str, query: dict | None = None, body: bytes | None = None) -> bytes:
    url = base_url.rstrip("/") + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(url, data=body if method == "POST" else None, headers=headers, method=method)
    if method == "POST" and body is None:
        req.data = b""
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return res.read()
    except urllib.error.HTTPError as e:
        raise VoiceError(f"VOICEVOX Engine が {path} を拒んだ: HTTP {e.code}") from e
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
        raise VoiceError(f"VOICEVOX Engine（{base_url}）に繋がらない。{START_HINT}") from e


def synthesize(text: str, speaker: int, base_url: str) -> bytes:
    query = _request("POST", base_url, "/audio_query", {"text": text, "speaker": speaker})
    return _request("POST", base_url, "/synthesis", {"speaker": speaker}, query)


def engine_version(base_url: str) -> str:
    return str(json.loads(_request("GET", base_url, "/version")))


def speakers(base_url: str) -> list[dict]:
    return json.loads(_request("GET", base_url, "/speakers"))


def speaker_name(base_url: str, speaker: int) -> str:
    for s in speakers(base_url):
        if any(style["id"] == speaker for style in s["styles"]):
            return s["name"]
    raise VoiceError(f"話者 {speaker} が Engine に無い（--list-speakers で一覧を見る）")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def build(items_path: Path, out_dir: Path, speaker: int, base_url: str) -> list[Path]:
    """voice/<id>.wav を作り、manifest.json に記録する。作った（作り直した）ファイルの一覧を返す。"""
    try:
        data = json.loads(Path(items_path).read_text(encoding="utf-8"))
        items = [(i["id"], i["reading"]) for i in data["items"]]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        raise VoiceError(f"{items_path}: items.json として読めない: {e}") from e

    version = engine_version(base_url)
    name = speaker_name(base_url, speaker)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    previous = _load_manifest(manifest_path)
    same_voice = previous.get("speaker") == speaker and previous.get("engine_version") == version
    old_files = previous.get("files", {}) if same_voice else {}

    files: dict[str, dict] = {}
    written: list[Path] = []
    for item_id, reading in items:
        dest = out_dir / f"{item_id}.wav"
        old = old_files.get(item_id)
        if old and old.get("text") == reading and dest.is_file() and _sha256(dest.read_bytes()) == old.get("sha256"):
            files[item_id] = old
            continue
        wav = synthesize(reading, speaker, base_url)
        dest.write_bytes(wav)
        files[item_id] = {"text": reading, "sha256": _sha256(wav)}
        written.append(dest)

    keep = {f"{item_id}.wav" for item_id, _ in items}
    for old_wav in out_dir.glob("*.wav"):
        if old_wav.name not in keep:
            old_wav.unlink()
    manifest = {"speaker": speaker, "speaker_name": name, "engine_version": version, "files": files}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return written


def trial(speaker_ids: list[int], out_dir: Path, base_url: str) -> list[Path]:
    """試聴用に、話者ごとに TRIAL_TEXTS の声を out_dir/<話者>/<名前>.wav に作る（共通素材には入れない）。"""
    written = []
    for sid in speaker_ids:
        for key, text in TRIAL_TEXTS.items():
            dest = Path(out_dir) / str(sid) / f"{key}.wav"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(synthesize(text, sid, base_url))
            written.append(dest)
    return written


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VOICEVOX で名前の声を作る")
    parser.add_argument("--speaker", type=int, help="話者（スタイル）の ID。共通素材の声を作る")
    parser.add_argument("--list-speakers", action="store_true")
    parser.add_argument("--trial", action="store_true", help="試聴用の声を作る（--speakers と --out が要る）")
    parser.add_argument("--speakers", type=int, nargs="*", default=[])
    parser.add_argument("--items", type=Path, default=DEFAULT_ITEMS)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    base_url = os.environ.get("VOICEVOX_URL", DEFAULT_URL)
    try:
        if args.list_speakers:
            for s in speakers(base_url):
                styles = ", ".join(f"{st['name']}={st['id']}" for st in s["styles"])
                print(f"{s['name']}: {styles}")
            return 0
        if args.trial:
            if not args.speakers or args.out is None:
                parser.error("--trial には --speakers と --out が要る")
            for p in trial(args.speakers, args.out, base_url):
                print(f"作った: {p}")
            return 0
        if args.speaker is None:
            parser.error("--speaker（または --list-speakers・--trial）が要る")
        written = build(args.items, args.out or DEFAULT_OUT, args.speaker, base_url)
        print(f"作った: {len(written)} 個（作り直さなかった声は含まない）")
        return 0
    except VoiceError as e:
        print(f"止まった: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
