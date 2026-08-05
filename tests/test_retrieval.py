import json

from fiesc_pm.retrieval import KnowledgeBase


def test_retrieval_is_filtered_by_fault_family(tmp_path) -> None:
    payload = {
        "registry": {"bearing": "Doc1.pdf", "belt": "Doc4.pdf"},
        "documents": {},
        "chunks": [
            {
                "citation_id": "DOC1-P001-C01",
                "fault_family": "bearing",
                "document": "Doc1.pdf",
                "page": 1,
                "section": "Rolamentos",
                "text": "Inspecionar rolamento, lubrificacao e folga conforme fabricante.",
            },
            {
                "citation_id": "DOC4-P001-C01",
                "fault_family": "belt",
                "document": "Doc4.pdf",
                "page": 1,
                "section": "Correias",
                "text": "Verificar tensao e alinhamento da correia.",
            },
        ],
    }
    path = tmp_path / "knowledge.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    knowledge = KnowledgeBase(path)
    result = knowledge.retrieve("bearing", "rolamento e lubrificacao", top_k=2)
    assert result
    assert all(citation.document == "Doc1.pdf" for citation in result)


def test_missing_document_is_explicit(tmp_path) -> None:
    payload = {
        "registry": {"fan": None, "bearing": "Doc1.pdf"},
        "documents": {},
        "chunks": [
            {
                "citation_id": "DOC1-P001-C01",
                "fault_family": "bearing",
                "document": "Doc1.pdf",
                "page": 1,
                "section": "Rolamentos",
                "text": "Inspecionar rolamento.",
            }
        ],
    }
    path = tmp_path / "knowledge.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    knowledge = KnowledgeBase(path)
    assert not knowledge.has_document("fan")
    assert knowledge.retrieve("fan", "ventoinha") == []
