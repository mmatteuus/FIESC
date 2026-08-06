from __future__ import annotations

import getpass
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"
KEY_NAME = "GEMINI_API_KEY"
DEFAULT_MODEL = "gemini-3.6-flash"


def _upsert(lines: list[str], name: str, value: str) -> list[str]:
    prefix = f"{name}="
    updated: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(prefix):
            updated.append(f"{prefix}{value}")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        if updated and updated[-1].strip():
            updated.append("")
        updated.append(f"{prefix}{value}")
    return updated


def main() -> None:
    key = getpass.getpass("Cole a GEMINI_API_KEY da demonstração: ").strip()
    if not key:
        raise SystemExit("Chave vazia; nenhuma alteração foi feita.")
    if any(character in key for character in "\r\n\x00"):
        raise SystemExit("Chave inválida; nenhuma alteração foi feita.")

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    lines = _upsert(lines, KEY_NAME, key)
    lines = _upsert(lines, "GEMINI_MODEL", os.getenv("GEMINI_MODEL", DEFAULT_MODEL))
    ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    if os.name != "nt":
        ENV_PATH.chmod(0o600)
    print("GEMINI_API_KEY configurada no .env local. O valor não foi exibido.")


if __name__ == "__main__":
    main()
