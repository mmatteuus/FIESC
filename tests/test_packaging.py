from __future__ import annotations

from scripts.package_release import release_files


def test_release_excludes_generated_files() -> None:
    names = [path.as_posix() for path in release_files()]
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)
    assert not any(".egg-info/" in name for name in names)
