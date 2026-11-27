"""VOICEVOX Engine で、共通素材の名前の声（voice/<id>.wav）と、決まり文句の声（voice/ask-<id>.wav など）を作る。

決まり文句の文・アクセントの直しは shared-assets/tools/phrases.json（ゲームには配らない）。

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
import copy
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
DEFAULT_PHRASES = ROOT / "shared-assets" / "tools" / "phrases.json"
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


def apply_contour(query: dict, contour: dict) -> bool:
    """アクセント句 contour["phrase"]（負の数は後ろから）の mora の pitch を、基準 + offsets[i] にする。

    基準は、ほかのアクセント句の、声のある mora（pitch > 0）の平均。ほかに無ければ、その句の平均。
    contour["base"] があれば、それを基準にする（名前の声そのものの高さを決めるとき）。
    pitch は対数の高さで、0.0578 が半音（ln2 / 12）。mora の数と offsets の数が違えば VoiceError。

    contour["rise"] = {"offset": 差, "seconds": 長さ} があれば、その句の最後の mora の母音を伸ばした音を
    1 つ足し、基準 + offset の高さにする（「？」の上がり）。Engine の自動の上がりと二重にならないよう、
    その句の is_interrogative は False にする。足したときは True を返す（合成で自動の上がりを切るため）。
    """
    phrases = query["accent_phrases"]
    index, offsets = contour["phrase"], contour["offsets"]
    if not -len(phrases) <= index < len(phrases):
        raise VoiceError(f"contour の phrase {index} が無い（アクセント句は {len(phrases)} 個）")
    target = phrases[index]
    moras = target["moras"]
    if len(moras) != len(offsets):
        raise VoiceError(f"contour の offsets が {len(offsets)} 個だが、その句の mora は {len(moras)} 個")
    others = [
        m["pitch"] for i, p in enumerate(phrases) if i != index % len(phrases) for m in p["moras"] if m["pitch"] > 0
    ]
    own = [m["pitch"] for m in moras if m["pitch"] > 0]
    pool = others or own
    base = contour["base"] if "base" in contour else (sum(pool) / len(pool) if pool else 0.0)
    for mora, offset in zip(moras, offsets):
        mora["pitch"] = base + offset
    rise = contour.get("rise")
    if rise is not None:
        up = copy.deepcopy(moras[-1])
        up.update(
            {
                "consonant": None,
                "consonant_length": None,
                "vowel_length": rise["seconds"],
                "pitch": base + rise["offset"],
            }
        )
        moras.append(up)
        target["is_interrogative"] = False
    # 名前の高さは、決まり文句の部分を決めたあとで直す（決まり文句の基準が、名前ごとに動かないように）
    name = contour.get("name")
    if name is not None:
        name_index = contour["name_phrase"]
        if not -len(phrases) <= name_index < len(phrases):
            raise VoiceError(f"contour の name_phrase {name_index} が無い（アクセント句は {len(phrases)} 個）")
        name_moras = phrases[name_index]["moras"]
        if len(name_moras) < len(name["offsets"]):
            raise VoiceError(f"contour の name の offsets が {len(name['offsets'])} 個だが、名前の句の mora は {len(name_moras)} 個")
        for mora, offset in zip(name_moras, name["offsets"]):
            mora["pitch"] = name["base"] + offset
    return rise is not None


def synthesize(
    text: str, speaker: int, base_url: str, is_kana: bool = False, contour: dict | None = None
) -> bytes:
    """is_kana=True なら text を AquesTalk 風の読み（' がアクセント、/ が区切り、? が疑問）として渡す。
    contour があれば、合成の前に、アクセント句の pitch を apply_contour で決める。"""
    params: dict = {"text": text, "speaker": speaker}
    if is_kana:
        params["is_kana"] = "true"
    query = _request("POST", base_url, "/audio_query", params)
    synthesis_params: dict = {"speaker": speaker}
    if contour is not None:
        data = json.loads(query)
        if apply_contour(data, contour):
            synthesis_params["enable_interrogative_upspeak"] = "false"  # 上がりは contour の rise で決めた
        query = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return _request("POST", base_url, "/synthesis", synthesis_params, query)


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


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise VoiceError(f"キー '{key}' が重複している")
        result[key] = value
    return result


def load_phrases(
    phrases_path: Path, items: list[tuple[str, str]]
) -> tuple[list[tuple[str, str, bool, dict | None]], dict[str, dict]]:
    """phrases.json から、決まり文句の (ファイルの名前, 読む文字列, かな指定か, 抑揚) の一覧と、
    名前の声そのものの抑揚（項目の id → contour）を作る。形が違えば、どの項目かを示す VoiceError。

    templates は全項目に当てはめて `<キー>-<id>`、single は `<キー>`、kana は名前ごとの上書き（AquesTalk 風）。
    text は名前ごとの、Engine に渡す文の書き直し（kana より弱い）。
    contour は templates・single のキーごとの抑揚（apply_contour。{"phrase": 句の番号, "offsets": [mora ごとの差]}）。
    """
    where = str(phrases_path)
    try:
        data = json.loads(Path(phrases_path).read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    except OSError as e:
        raise VoiceError(f"{where}: 読めない: {e}") from e
    except json.JSONDecodeError as e:
        raise VoiceError(f"{where}: JSON として読めない: {e}") from e
    except VoiceError as e:
        raise VoiceError(f"{where}: {e}") from e
    if not isinstance(data, dict):
        raise VoiceError(f"{where}: オブジェクトでない")

    templates = data.get("templates")
    if not isinstance(templates, dict) or not templates:
        raise VoiceError(f"{where}: templates が、空でないオブジェクトでない")
    single = data.get("single", {})
    kana = data.get("kana", {})
    if not isinstance(single, dict):
        raise VoiceError(f"{where}: single がオブジェクトでない")
    if not isinstance(kana, dict):
        raise VoiceError(f"{where}: kana がオブジェクトでない")

    for key, template in templates.items():
        if not isinstance(template, str) or "{reading}" not in template:
            raise VoiceError(f"{where}: templates.{key} に {{reading}} が無い")
    for key, text in single.items():
        if key in templates:
            raise VoiceError(f"{where}: single.{key} が templates と重複している")
        if not isinstance(text, str) or not text:
            raise VoiceError(f"{where}: single.{key} が空でない文字列でない")

    contours = data.get("contour", {})
    if not isinstance(contours, dict):
        raise VoiceError(f"{where}: contour がオブジェクトでない")
    for key, spec in contours.items():
        if key not in templates and key not in single:
            raise VoiceError(f"{where}: contour.{key} が、templates にも single にも無い")
        if not isinstance(spec, dict):
            raise VoiceError(f"{where}: contour.{key} がオブジェクトでない")
        offsets = spec.get("offsets")
        if (
            not isinstance(spec.get("phrase"), int)
            or isinstance(spec.get("phrase"), bool)
            or not isinstance(offsets, list)
            or not offsets
            or not all(_is_number(o) for o in offsets)
        ):
            raise VoiceError(f"{where}: contour.{key} は {{\"phrase\": 整数, \"offsets\": [数, ...]}} の形でない")
        rise = spec.get("rise")
        if rise is not None and not (
            isinstance(rise, dict)
            and _is_number(rise.get("offset"))
            and _is_number(rise.get("seconds"))
            and rise["seconds"] > 0
        ):
            raise VoiceError(f"{where}: contour.{key}.rise は {{\"offset\": 数, \"seconds\": 正の数}} の形でない")

    item_ids = {item_id for item_id, _ in items}
    name_contours = data.get("name_contour", {})
    if not isinstance(name_contours, dict):
        raise VoiceError(f"{where}: name_contour がオブジェクトでない")
    for item_id, step in name_contours.items():
        if item_id not in item_ids:
            raise VoiceError(f"{where}: name_contour.{item_id} が、items.json に無い")
        if not (
            isinstance(step, dict)
            and _is_number(step.get("base"))
            and isinstance(step.get("offsets"), list)
            and step["offsets"]
            and all(_is_number(o) for o in step["offsets"])
        ):
            raise VoiceError(f"{where}: name_contour.{item_id} は {{\"base\": 数, \"offsets\": [数, ...]}} の形でない")
    for key, spec in contours.items():
        if "name_phrase" in spec and (not isinstance(spec["name_phrase"], int) or isinstance(spec["name_phrase"], bool)):
            raise VoiceError(f"{where}: contour.{key}.name_phrase が整数でない")

    def contour_of(key: str, item_id: str | None) -> dict | None:
        spec = contours.get(key)
        if item_id is None or item_id not in name_contours:
            return spec
        if spec is None or "name_phrase" not in spec:
            raise VoiceError(f"{where}: name_contour.{item_id} を使うには、contour.{key} に name_phrase が要る")
        return {**spec, "name": name_contours[item_id]}

    entries: list[tuple[str, str, bool, dict | None]] = []
    for key, template in templates.items():
        for item_id, reading in items:
            entries.append(
                (f"{key}-{item_id}", template.replace("{reading}", reading), False, contour_of(key, item_id))
            )
    for key, text in single.items():
        entries.append((key, text, False, contours.get(key)))

    names = {name for name, _, _, _ in entries}
    item_ids = {item_id for item_id, _ in items}
    clash = sorted(names & item_ids)
    if clash:
        raise VoiceError(f"{where}: 名前の声と同じ名前のファイルができる: {clash[0]}")
    texts = data.get("text", {})
    if not isinstance(texts, dict):
        raise VoiceError(f"{where}: text がオブジェクトでない")
    for section, overrides in (("kana", kana), ("text", texts)):
        for name, text in overrides.items():
            if name not in names:
                raise VoiceError(f"{where}: {section}.{name} が、作るファイルの名前に無い")
            if not isinstance(text, str) or not text:
                raise VoiceError(f"{where}: {section}.{name} が空でない文字列でない")
    # 優先は kana > text > 型から作った文。text は、Engine が読み誤る名前の書き直し（例: ぞうは → 象派 と読まれる）
    # 名前の声そのもの（<id>.wav）にも、同じ高さを効かせる（決まり文句の中の名前と、食い違わないように）
    name_voice_contours = {
        item_id: {"phrase": 0, "offsets": step["offsets"], "base": step["base"]} for item_id, step in name_contours.items()
    }
    phrase_entries = [
        (name, kana.get(name, texts.get(name, text)), name in kana, contour) for name, text, _, contour in entries
    ]
    return phrase_entries, name_voice_contours


def build(
    items_path: Path, out_dir: Path, speaker: int, base_url: str, phrases_path: Path | None = None
) -> list[Path]:
    """voice/<id>.wav（と、phrases_path があれば決まり文句の wav）を作り、manifest.json に記録する。作った（作り直した）ファイルの一覧を返す。"""
    try:
        data = json.loads(Path(items_path).read_text(encoding="utf-8"))
        items = [(i["id"], i["reading"]) for i in data["items"]]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        raise VoiceError(f"{items_path}: items.json として読めない: {e}") from e
    phrase_entries: list[tuple[str, str, bool, dict | None]] = []
    name_voice_contours: dict[str, dict] = {}
    if phrases_path is not None:
        phrase_entries, name_voice_contours = load_phrases(phrases_path, items)
    entries = [(item_id, reading, False, name_voice_contours.get(item_id)) for item_id, reading in items]
    entries += phrase_entries

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
    for file_id, text, is_kana, contour in entries:
        dest = out_dir / f"{file_id}.wav"
        old = old_files.get(file_id)
        if (
            old
            and old.get("text") == text
            and bool(old.get("kana")) == is_kana
            and old.get("contour") == contour
            and dest.is_file()
            and _sha256(dest.read_bytes()) == old.get("sha256")
        ):
            files[file_id] = old
            continue
        try:
            wav = synthesize(text, speaker, base_url, is_kana, contour)
        except VoiceError as e:
            raise VoiceError(f"{file_id}: {e}") from e
        dest.write_bytes(wav)
        files[file_id] = {"text": text, "sha256": _sha256(wav)}
        if is_kana:
            files[file_id]["kana"] = True
        if contour is not None:
            files[file_id]["contour"] = contour
        written.append(dest)

    keep = {f"{file_id}.wav" for file_id, _, _, _ in entries}
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
    parser.add_argument("--phrases", type=Path, default=DEFAULT_PHRASES, help="決まり文句の定義（phrases.json）")
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
        written = build(args.items, args.out or DEFAULT_OUT, args.speaker, base_url, args.phrases)
        print(f"作った: {len(written)} 個（作り直さなかった声は含まない）")
        return 0
    except VoiceError as e:
        print(f"止まった: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
