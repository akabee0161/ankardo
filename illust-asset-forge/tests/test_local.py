import re
import subprocess

import pytest

from artgen.config import ConfigError
from artgen.local import local_commit, local_dirs, save_outputs


def test_local_dirs(tmp_path):
    d = local_dirs(tmp_path)
    assert d.runs == tmp_path / "local" / "runs"
    assert d.selected == tmp_path / "local" / "selected"
    assert d.packs == tmp_path / "local" / "packs"
    assert d.rounds == tmp_path / "local" / "rounds"
    assert not (tmp_path / "local").exists()  # 作るのは書く側


def _git(root, *args):
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        check=True, capture_output=True,
    )


def test_local_commit_clean_and_dirty(tmp_path):
    _git(tmp_path, "init", "-q")
    (tmp_path / "x.txt").write_text("a")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "init")
    assert re.fullmatch(r"[0-9a-f]{7,}", local_commit(tmp_path))
    (tmp_path / "x.txt").write_text("changed")
    clean = local_commit(tmp_path)
    assert re.fullmatch(r"[0-9a-f]{7,}\+dirty", clean)


def test_local_commit_ignores_changes_outside_root(tmp_path):
    _git(tmp_path, "init", "-q")
    sub = tmp_path / "forge"
    sub.mkdir()
    (sub / "a.txt").write_text("a")
    (tmp_path / "other.txt").write_text("o")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "init")
    (tmp_path / "other.txt").write_text("changed")
    assert not local_commit(sub).endswith("+dirty")
    (sub / "a.txt").write_text("changed")
    assert local_commit(sub).endswith("+dirty")


def test_local_commit_without_git(tmp_path):
    assert local_commit(tmp_path) == "unknown"


def test_save_outputs_writes_relative(tmp_path):
    paths = save_outputs(tmp_path, [("c1/face/20261123_120000/c1_face_1.png", b"png")])
    assert paths == [tmp_path / "c1/face/20261123_120000/c1_face_1.png"]
    assert paths[0].read_bytes() == b"png"


@pytest.mark.parametrize("bad", ["/etc/x.png", "../x.png", "c1/../../x.png"])
def test_save_outputs_rejects_escape(tmp_path, bad):
    with pytest.raises(ConfigError):
        save_outputs(tmp_path / "runs", [("ok/a.png", b"1"), (bad, b"2")])
    assert not (tmp_path / "runs").exists()  # 1 つでも悪ければ何も書かない


def test_save_outputs_does_not_replace_existing_images(tmp_path):
    existing = tmp_path / "c1/face/r/c1_face_1.png"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"old")
    with pytest.raises(ConfigError, match="既にある"):
        save_outputs(tmp_path, [("c1/face/r/c1_face_2.png", b"2"), ("c1/face/r/c1_face_1.png", b"new")])
    assert existing.read_bytes() == b"old"
    assert not (tmp_path / "c1/face/r/c1_face_2.png").exists()  # 1 つでも既にあれば何も書かない


def test_save_outputs_removes_its_files_when_a_write_fails(tmp_path, monkeypatch):
    # 2 枚目の書き込みが容量不足などで失敗したら、1 枚目と書きかけの 2 枚目を残さない（再試行が既存の検査で止まらない）
    from pathlib import Path

    real_open = Path.open

    def failing_open(self, mode="r", *args, **kwargs):
        f = real_open(self, mode, *args, **kwargs)
        if self.name == "b.png":
            class Broken:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, *exc):
                    f.close()

                def write(self_inner, data):
                    f.write(data[:1])
                    raise OSError(28, "No space left on device")
            return Broken()
        return f

    monkeypatch.setattr(Path, "open", failing_open)
    with pytest.raises(OSError, match="No space"):
        save_outputs(tmp_path / "runs", [("c1/a.png", b"1"), ("c1/b.png", b"22")])
    assert not (tmp_path / "runs/c1/a.png").exists()
    assert not (tmp_path / "runs/c1/b.png").exists()
