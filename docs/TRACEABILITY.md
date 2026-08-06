# Matriz de rastreabilidade

| Requisito | Implementação | Evidência |
|---|---|---|
| Pipeline completo de IA | `src/fiesc_pm` | `tests/test_service_integration.py` e teste rápido |
| Arquitetura de implantação | `docs/ARQUITETURA.md` | Diagramas MVP e industrial |
| Processamento de documentos | `retrieval.py` | 74 trechos, página, método e hash no índice |
| Sugestão de correção | `llm.py` e `service.py` | Resposta com citações validadas |
| Recusa sem documento | Gate em `service.py` | Testes para rotor excêntrico e perda de fase |
| Visualizações | `app/streamlit_app.py` | Cinco áreas e seis cenários |
| Recorrência e contexto | `service.py` e aba Evidências | Contagem, período, frequência, condição e RPM dos eventos semelhantes |
| Teste independente | `modeling.py` | Sessões disjuntas de treino, seleção e teste em `metrics.json` |
| Python obrigatório | `pyproject.toml` | Python 3.12, `.venv` e CI |
| Controle de alucinação | Gate, esquema e fontes | Testes de prompt/citação e integração |
| Segurança do pacote | `.gitignore` e `security_check.py` | Varredura de segredos, PII e limite de 5 MB |
| Entregáveis | Relatório, apresentação e ZIP | PDFs renderizados e manifesto SHA-256 |
