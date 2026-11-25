"""このサーバー（Modal を呼ぶ側）の置き場と、条件に残す commit。

候補・採用した絵はリポジトリに入れない `local/` に置く。Drive の置き場（Colab の道）とは別。
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from artgen.config import ConfigError

LOCAL_DIR = "local"


@dataclass(frozen=True)
class LocalDirs:
    runs: Path
    selected: Path
    packs: Path
    rounds: Path
    installed: Path


def local_dirs(root: Path) -> LocalDirs:
    """`root/local/` の下の置き場。作りはしない（作るのは書く側）。"""
    base = Path(root) / LOCAL_DIR
    return LocalDirs(
        runs=base / "runs", selected=base / "selected", packs=base / "packs", rounds=base / "rounds",
        installed=base / "installed",
    )


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True, timeout=10,
    )
    return out.stdout.strip()


def local_commit(root: Path) -> str:
    """HEAD の短い commit。root の下に未コミットの変更があれば末尾に `+dirty`。git が使えなければ "unknown"。"""
    try:
        commit = _git(root, "rev-parse", "--short", "HEAD")
        if not commit:
            return "unknown"
        return commit + ("+dirty" if _git(root, "status", "--porcelain", "--", ".") else "")
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def save_outputs(runs_dir: Path, outputs: list[tuple[str, bytes]]) -> list[Path]:
    """outputs（runs/ からの相対パスとバイト）を書く。既にある絵は置き換えない。

    1 つでも悪いパス・既にあるパスがあれば何も書かずに ConfigError。調べた後に別の実行が同じパスを
    書いたときも置き換えず ConfigError で止める（そのときは、この実行で書いた分だけを消す）。
    """
    runs_dir = Path(runs_dir)
    targets: list[tuple[Path, bytes]] = []
    for rel, data in outputs:
        posix = PurePosixPath(rel)
        if posix.is_absolute() or ".." in posix.parts or not posix.parts:
            raise ConfigError(f"outputs: runs/ の外を指すパス: {rel!r}")
        targets.append((runs_dir.joinpath(*posix.parts), data))
    existing = [p for p, _ in targets if p.exists()]
    if existing:
        raise ConfigError(f"outputs: 同じ名前の絵が既にある（置き換えない）: {', '.join(map(str, existing))}")
    written: list[Path] = []
    try:
        for path, data in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as f:
                written.append(path)
                f.write(data)
    except OSError as e:
        # この実行で作ったファイル（書きかけを含む）だけを消す。開けなかった（別の実行の）パスは written に入っていない
        for p in written:
            p.unlink(missing_ok=True)
        if isinstance(e, FileExistsError):
            raise ConfigError(f"outputs: 同じ名前の絵を別の実行が先に書いた（置き換えない）: {path}") from e
        raise
    return [p for p, _ in targets]
