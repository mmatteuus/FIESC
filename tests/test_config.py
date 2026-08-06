from pathlib import Path

from fiesc_pm.config import get_settings


def test_vercel_runtime_uses_temporary_directory(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("FIESC_RUNTIME_DIR", raising=False)
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.runtime_dir == Path("/tmp/fiesc-runtime")
        assert settings.database_path == Path("/tmp/fiesc-runtime/audit.sqlite3")
    finally:
        get_settings.cache_clear()
