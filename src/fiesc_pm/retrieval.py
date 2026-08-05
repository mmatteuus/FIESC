from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import fitz
import numpy as np
import pytesseract
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .schemas import Citation

DOCUMENT_REGISTRY: dict[str, str | None] = {
    "bearing": "Doc1.pdf",
    "misalignment": "Doc2.pdf",
    "imbalance": "Doc3.pdf",
    "belt": "Doc4.pdf",
    "pulley": "Doc5.pdf",
    "cocked_rotor": "Doc6.pdf",
    "eccentric_rotor": None,
    "fan": None,
    "phase_loss": None,
    "normal": None,
}


@dataclass(frozen=True)
class KnowledgeChunk:
    citation_id: str
    fault_family: str
    document: str
    page: int
    section: str
    text: str
    source_sha256: str
    extraction: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _clean_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _chunk_text(text: str, target: int = 900, overlap: int = 120) -> list[str]:
    if len(text) <= target:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + target)
        if end < len(text):
            boundary = text.rfind(" ", start + target // 2, end)
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def build_knowledge_index(
    source_dir: Path,
    output_path: Path,
    tesseract_cmd: str,
    tessdata_prefix: str,
) -> dict[str, Any]:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    if tessdata_prefix:
        os.environ["TESSDATA_PREFIX"] = tessdata_prefix
    chunks: list[KnowledgeChunk] = []
    document_stats: dict[str, Any] = {}

    for family, filename in DOCUMENT_REGISTRY.items():
        if not filename:
            continue
        path = source_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Documento registrado nao encontrado: {path}")
        source_hash = _sha256(path)
        pdf = fitz.open(path)
        pages_with_ocr = 0
        document_chars = 0
        for page_number, page in enumerate(pdf, start=1):
            text = _clean_text(page.get_text("text"))
            extraction = "text_layer"
            if len(text) < 80:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                tessdata_arg = f' --tessdata-dir "{tessdata_prefix}"' if tessdata_prefix else ""
                text = _clean_text(
                    pytesseract.image_to_string(
                        image,
                        lang="por+eng",
                        config=f"--psm 6{tessdata_arg}",
                    )
                )
                extraction = "ocr_tesseract"
                pages_with_ocr += 1
            document_chars += len(text)
            pieces = _chunk_text(text)
            section = pieces[0].split("\n", 1)[0][:100] if pieces else f"Pagina {page_number}"
            for chunk_number, piece in enumerate(pieces, start=1):
                chunks.append(
                    KnowledgeChunk(
                        citation_id=f"{path.stem.upper()}-P{page_number:03d}-C{chunk_number:02d}",
                        fault_family=family,
                        document=path.name,
                        page=page_number,
                        section=section,
                        text=piece,
                        source_sha256=source_hash,
                        extraction=extraction,
                    )
                )
        document_stats[path.name] = {
            "fault_family": family,
            "pages": len(pdf),
            "pages_with_ocr": pages_with_ocr,
            "characters": document_chars,
            "sha256": source_hash,
        }
        pdf.close()

    payload = {
        "schema_version": 1,
        "registry": DOCUMENT_REGISTRY,
        "documents": document_stats,
        "chunks": [asdict(chunk) for chunk in chunks],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


class KnowledgeBase:
    def __init__(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.registry: dict[str, str | None] = payload["registry"]
        self.documents: dict[str, Any] = payload["documents"]
        self.chunks: list[dict[str, Any]] = payload["chunks"]
        self.vectorizer = TfidfVectorizer(
            strip_accents="unicode", ngram_range=(1, 2), max_features=12_000, sublinear_tf=True
        )
        texts = [chunk["text"] for chunk in self.chunks]
        self.matrix = self.vectorizer.fit_transform(texts)

    def has_document(self, fault_family: str) -> bool:
        return bool(self.registry.get(fault_family))

    def retrieve(self, fault_family: str, query: str, top_k: int = 3) -> list[Citation]:
        allowed = [
            index
            for index, chunk in enumerate(self.chunks)
            if chunk["fault_family"] == fault_family
        ]
        if not allowed:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix[allowed]).ravel()
        order = np.argsort(scores)[::-1][:top_k]
        citations: list[Citation] = []
        for position in order:
            chunk = self.chunks[allowed[int(position)]]
            citations.append(
                Citation(
                    citation_id=chunk["citation_id"],
                    document=chunk["document"],
                    page=int(chunk["page"]),
                    section=chunk["section"],
                    excerpt=chunk["text"][:650],
                    score=float(scores[int(position)]),
                )
            )
        return citations
