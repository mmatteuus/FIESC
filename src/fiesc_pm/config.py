from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env", override=False)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default.resolve()
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    source_dir: Path
    artifacts_dir: Path
    runtime_dir: Path
    model_path: Path
    metadata_path: Path
    knowledge_path: Path
    metrics_path: Path
    database_path: Path
    api_key: str | None
    gemini_api_key: str | None
    gemini_model: str
    ollama_base_url: str
    ollama_model: str
    enable_ollama_fallback: bool
    tesseract_cmd: str
    tessdata_prefix: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    artifacts = REPO_ROOT / "artifacts"
    runtime_default = Path("/tmp/fiesc-runtime") if os.getenv("VERCEL") else REPO_ROOT / "runtime"
    runtime = _resolve_path(os.getenv("FIESC_RUNTIME_DIR"), runtime_default)
    source_default = REPO_ROOT.parent / "_privado" / "fontes"
    return Settings(
        repo_root=REPO_ROOT,
        source_dir=_resolve_path(os.getenv("FIESC_SOURCE_DIR"), source_default),
        artifacts_dir=artifacts,
        runtime_dir=runtime,
        model_path=artifacts / "model_bundle.joblib",
        metadata_path=artifacts / "model_metadata.json",
        knowledge_path=artifacts / "knowledge_index.json",
        metrics_path=artifacts / "metrics.json",
        database_path=runtime / "audit.sqlite3",
        api_key=os.getenv("FIESC_API_KEY") or None,
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
        enable_ollama_fallback=_env_bool("ENABLE_OLLAMA_FALLBACK", False),
        tesseract_cmd=os.getenv("TESSERACT_CMD") or shutil.which("tesseract") or "tesseract",
        tessdata_prefix=os.getenv("TESSDATA_PREFIX", ""),
    )
