from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "release" / "Mateus_Ferreira_Lopes_FIESC_02198_Codigo.zip"
MAX_BYTES = 5 * 1024 * 1024

ROOT_FILES = {
    ".dockerignore",
    ".env.example",
    ".gitignore",
    "Dockerfile",
    "README.md",
    "pyproject.toml",
    "requirements-app.txt",
    "requirements-dev.txt",
    "requirements-documents.txt",
    "requirements.txt",
}
ALLOWED_ROOTS = {
    ".github",
    ".streamlit",
    "app",
    "artifacts",
    "data/demo",
    "docs",
    "scripts",
    "src",
    "tests",
}
FORBIDDEN_SUFFIXES = {".csv", ".docx", ".pdf", ".env", ".key", ".pem"}
FORBIDDEN_NAMES = {
    "banner.csv",
    "cnh mateus ferreira.pdf",
    "certificado ensino medio.pdf",
    "comprovante_escolaridade_completo_mateus.pdf",
}
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "output",
    "runtime",
    "tmp",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def release_files() -> list[Path]:
    files = [ROOT / name for name in sorted(ROOT_FILES)]
    for relative in sorted(ALLOWED_ROOTS):
        directory = ROOT / relative
        if not directory.exists():
            continue
        files.extend(
            sorted(
                path
                for path in directory.rglob("*")
                if path.is_file()
                and not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
                and not any(part.endswith(".egg-info") for part in path.relative_to(ROOT).parts)
                and path.suffix.lower() not in EXCLUDED_SUFFIXES
            )
        )
    return sorted(set(files))


def validate(files: list[Path]) -> None:
    problems: list[str] = []
    for path in files:
        relative = path.relative_to(ROOT)
        if not path.exists():
            problems.append(f"Arquivo obrigatorio ausente: {relative}")
            continue
        if path.name.lower() in FORBIDDEN_NAMES:
            problems.append(f"Arquivo privado: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES and path.name != ".env.example":
            problems.append(f"Formato privado proibido: {relative}")
        if path.stat().st_size > MAX_BYTES:
            problems.append(f"Arquivo individual acima de 5 MB: {relative}")
        if EXCLUDED_PARTS.intersection(relative.parts) or path.name == ".env":
            problems.append(f"Caminho proibido: {relative}")
    if problems:
        raise SystemExit("\n".join(problems))


def main() -> None:
    files = release_files()
    validate(files)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    if OUTPUT.stat().st_size > MAX_BYTES:
        raise SystemExit(f"ZIP acima de 5 MB: {OUTPUT.stat().st_size}")
    manifest = {
        "file": OUTPUT.name,
        "bytes": OUTPUT.stat().st_size,
        "sha256": sha256(OUTPUT),
        "entries": len(files),
    }
    (OUTPUT.parent / "release_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
