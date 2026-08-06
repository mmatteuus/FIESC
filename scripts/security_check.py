from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {
    "banner.csv",
    "cnh mateus ferreira.pdf",
    "certificado ensino medio.pdf",
    "comprovante_escolaridade_completo_mateus.pdf",
}
FORBIDDEN_TRACKED_PARTS = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "output",
    "runtime",
    "tmp",
}
EXCLUDED_SCAN_PARTS = {".git", *FORBIDDEN_TRACKED_PARTS}
SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"AQ\.[0-9A-Za-z_-]{30,}"),
    re.compile(r"sk-[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?m)^[ \t]*(?:GEMINI_API_KEY|FIESC_API_KEY)[ \t]*=[ \t]*[^\s#][^\r\n]*$"),
]


def _git_files() -> tuple[list[Path], list[Path]]:
    tracked = subprocess.run(
        ["git", "ls-files", "--cached"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    candidates = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return (
        [ROOT / line for line in tracked.stdout.splitlines() if line],
        [ROOT / line for line in candidates.stdout.splitlines() if line],
    )


def candidate_files() -> tuple[list[Path], list[Path]]:
    try:
        return _git_files()
    except (FileNotFoundError, subprocess.CalledProcessError):
        candidates = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and not EXCLUDED_SCAN_PARTS.intersection(path.relative_to(ROOT).parts)
        ]
        return candidates, candidates


def main() -> None:
    problems: list[str] = []
    tracked, candidates = candidate_files()

    for path in tracked:
        relative = path.relative_to(ROOT)
        if FORBIDDEN_TRACKED_PARTS.intersection(relative.parts):
            problems.append(f"Caminho local versionado: {relative}")

    checked = 0
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if EXCLUDED_SCAN_PARTS.intersection(relative.parts):
            continue
        checked += 1
        if path.name.lower() in FORBIDDEN_NAMES:
            problems.append(f"Arquivo privado no pacote: {path.name}")
        if path.stat().st_size > 5 * 1024 * 1024:
            problems.append(f"Arquivo acima de 5 MB: {relative}")
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".joblib", ".pptx", ".pdf"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                problems.append(f"Possivel segredo em {relative}")

    if not checked:
        problems.append("Nenhum arquivo foi verificado")
    if problems:
        raise SystemExit("\n".join(sorted(set(problems))))
    print(f"Security check passed: {checked} files checked")


if __name__ == "__main__":
    main()
