from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {
    "banner.csv",
    "cnh mateus ferreira.pdf",
    "certificado ensino medio.pdf",
}
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "runtime",
    "output",
    "tmp",
}
SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"AQ\.[0-9A-Za-z_-]{30,}"),
    re.compile(r"sk-[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?m)^[ \t]*(?:GEMINI_API_KEY|FIESC_API_KEY)[ \t]*=[ \t]*[^\s#][^\r\n]*$"),
]


def candidate_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return [ROOT / line for line in result.stdout.splitlines() if line]
    except (FileNotFoundError, subprocess.CalledProcessError):
        return [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
        ]


def main() -> None:
    problems: list[str] = []
    checked = 0
    for path in candidate_files():
        if not path.exists() or not path.is_file():
            continue
        checked += 1
        if path.name.lower() in FORBIDDEN_NAMES:
            problems.append(f"Arquivo proibido no pacote: {path.name}")
        if path.stat().st_size > 5 * 1024 * 1024:
            problems.append(f"Arquivo acima de 5 MB: {path.relative_to(ROOT)}")
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".joblib", ".pptx", ".pdf"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                problems.append(f"Possivel segredo em {path.relative_to(ROOT)}")
    if not checked:
        problems.append("Nenhum arquivo foi verificado")
    if problems:
        raise SystemExit("\n".join(problems))
    print(f"Security check passed: {checked} files checked")


if __name__ == "__main__":
    main()
