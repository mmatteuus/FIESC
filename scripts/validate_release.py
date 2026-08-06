from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "release" / "Mateus_Ferreira_Lopes_FIESC_02198_Codigo.zip"
MAX_BYTES = 5 * 1024 * 1024

REQUIRED_FILES = {
    "README.md",
    "app/streamlit_app.py",
    "artifacts/knowledge_index.json",
    "artifacts/model_bundle.joblib",
    "artifacts/model_metadata.json",
    "data/demo/demo_events.json",
    "scripts/package_release.py",
    "scripts/security_check.py",
    "scripts/validate_release.py",
    "src/fiesc_pm/service.py",
    "tests/test_packaging.py",
}
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", "runtime", "tmp"}


def main() -> None:
    if not OUTPUT.exists():
        raise SystemExit(f"Pacote nao encontrado: {OUTPUT}")
    if OUTPUT.stat().st_size > MAX_BYTES:
        raise SystemExit("Pacote excede 5 MB")

    with zipfile.ZipFile(OUTPUT) as archive:
        names = set(archive.namelist())
        missing = sorted(REQUIRED_FILES - names)
        if missing:
            raise SystemExit(f"Arquivos ausentes no pacote: {missing}")
        forbidden = sorted(
            name
            for name in names
            if FORBIDDEN_PARTS.intersection(Path(name).parts)
            or name.endswith((".pyc", ".pyo"))
        )
        if forbidden:
            raise SystemExit(f"Arquivos proibidos no pacote: {forbidden[:10]}")
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"Entrada corrompida no ZIP: {bad}")
        with tempfile.TemporaryDirectory() as temporary:
            archive.extractall(temporary)
            manifest = json.loads(
                (Path(temporary) / "artifacts/model_metadata.json").read_text(encoding="utf-8")
            )
            if not manifest.get("model_sha256"):
                raise SystemExit("Metadados de integridade ausentes")

    print(f"Release validado: {OUTPUT.name} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
