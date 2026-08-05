from __future__ import annotations

import json

from fiesc_pm.config import get_settings
from fiesc_pm.retrieval import build_knowledge_index


def main() -> None:
    settings = get_settings()
    payload = build_knowledge_index(
        settings.source_dir,
        settings.knowledge_path,
        settings.tesseract_cmd,
        settings.tessdata_prefix,
    )
    summary = {
        "documents": payload["documents"],
        "chunks": len(payload["chunks"]),
        "output": str(settings.knowledge_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
