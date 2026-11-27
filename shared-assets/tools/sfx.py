"""共通素材の正解・不正解の音（sfx/correct.wav・sfx/wrong.wav）を作る。標準ライブラリだけ。

使い方（ankardo のルートで）:
    python shared-assets/tools/sfx.py [--out <出力先>]

自作の音で、同じ入力から必ず同じバイト列になる。やさしい音にするため、どちらも
ピークは満点の半分以下（声より小さい）、始まりと終わりは滑らかに 0 に戻す。
  correct: 2 音（ド→ソ）が上がる、明るく短い音
  wrong:   低めの 1 音が少し下がる、柔らかい音（ブザーにしない）
"""

from __future__ import annotations

import argparse
import io
import math
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "shared-assets" / "chiiku" / "sfx"
RATE = 22050
FULL = 32767


def _tone(seconds: float, freq_start: float, freq_end: float, attack: float, tau: float) -> list[float]:
    """正弦波 + 弱い 2 倍音。アタックのあと指数的に減衰し、最後の 25ms で 0 まで絞る。"""
    n = int(seconds * RATE)
    out: list[float] = []
    phase = 0.0
    fade = int(0.025 * RATE)
    for i in range(n):
        t = i / RATE
        freq = freq_start + (freq_end - freq_start) * (i / n)
        phase += 2 * math.pi * freq / RATE
        wave_ = math.sin(phase) + 0.25 * math.sin(2 * phase)
        env = min(1.0, t / attack) * math.exp(-t / tau)
        if i >= n - fade:
            env *= (n - 1 - i) / fade
        out.append(wave_ * env)
    return out


def _mix(parts: list[tuple[float, list[float]]]) -> list[float]:
    """(開始の秒, 波形) を重ねる。"""
    length = max(int(start * RATE) + len(w) for start, w in parts)
    mixed = [0.0] * length
    for start, w in parts:
        offset = int(start * RATE)
        for i, v in enumerate(w):
            mixed[offset + i] += v
    return mixed


def _to_wav(samples: list[float], peak: float) -> bytes:
    top = max(abs(s) for s in samples) or 1.0
    scale = peak * FULL / top
    pcm = struct.pack(f"<{len(samples)}h", *(int(round(s * scale)) for s in samples))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm)
    return buf.getvalue()


def render(name: str) -> bytes:
    """名前（correct・wrong）の音を、wav のバイト列で返す。"""
    if name == "correct":
        c5, g5 = 523.25, 783.99
        samples = _mix(
            [
                (0.0, _tone(0.16, c5, c5, attack=0.010, tau=0.07)),
                (0.14, _tone(0.30, g5, g5, attack=0.010, tau=0.10)),
            ]
        )
        return _to_wav(samples, peak=0.40)
    if name == "wrong":
        return _to_wav(_tone(0.32, 220.0, 196.0, attack=0.040, tau=0.12), peak=0.30)
    raise ValueError(f"知らない音の名前: {name}（correct・wrong）")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="正解・不正解の音を作る")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ("correct", "wrong"):
        (args.out / f"{name}.wav").write_bytes(render(name))
        print(f"作った: {args.out / f'{name}.wav'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
