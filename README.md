# FIESC 02198/2026 — Manutenção Prescritiva Auditável

Solução desenvolvida para o estudo de caso da vaga **Desenvolvedor Full Stack - Pleno - IA e Python**. O projeto transforma sinais de vibração, temperatura e rotação em uma decisão rastreável: classifica a condição, compara eventos históricos, consulta a documentação técnica disponível e se abstém quando não há evidência suficiente.

> O sistema apoia a decisão. Nenhuma saída substitui inspeção, bloqueio e etiquetagem, procedimento do fabricante ou aprovação de profissional qualificado.

## Visão geral

```text
evento industrial
  → validação e preparação de 30 atributos
  → classificação da condição
  → confiança e detecção de novidade
  → comparação com eventos históricos
  → verificação de cobertura documental
  → recuperação de trechos por família e página
  → recomendação citada ou abstenção segura
  → registro de auditoria
```

A mesma regra de negócio atende:

- **interface web** para demonstração;
- **dashboard Streamlit** para exploração técnica;
- **API FastAPI** para integração;
- **scripts de validação** para reproduzir a entrega.

## Diferenciais demonstráveis

- 166.796 registros e 26 colunas auditados; 151 rótulos brutos consolidados em 10 famílias.
- Validação por sessões de aquisição, evitando duplicatas entre treino e validação.
- `id`, `created_at`, Fahrenheit e polegadas/s excluídos do modelo para reduzir vazamento e redundância.
- Baseline, regressão logística, Random Forest e HistGradientBoosting comparados.
- RAG por família, documento e página, com citações verificáveis.
- Expansão de consulta em português e descarte de resultados com relevância zero.
- Bloqueio anterior à geração da resposta: classe sem documento, baixa confiança, novidade ou operação normal interrompe o fluxo.
- Modo extrativo local sempre disponível; provedor generativo é opcional.
- Auditoria SQLite sem armazenar os sensores brutos completos.
- Pacote final validado automaticamente e limitado a 5 MB.

## Resultado do modelo

O modelo selecionado foi o **HistGradientBoosting**. No conjunto de teste independente por sessões, alcançou:

- macro F1: **0,415**;
- acurácia balanceada: **0,464**;
- acurácia: **0,514**;
- artefato compactado: aproximadamente **1,88 MB**.

Uma divisão aleatória atingiu macro F1 0,829, mas é apresentada apenas como diagnóstico, pois mistura contextos semelhantes e superestima a generalização. A etapa de seleção agrupada não contém registros da família `pulley`; essa limitação está registrada nos artefatos e deve ser considerada na evolução do modelo.

## Famílias documentadas e política de abstenção

Documentação disponível para:

- rolamento;
- desalinhamento;
- desbalanceamento;
- correia;
- polia;
- rotor inclinado.

Rotor excêntrico, ventilador e perda de fase são deliberadamente recusados por falta de documentação específica. Operação normal não gera recomendação corretiva.

## Execução local

Pré-requisitos:

- Python 3.12;
- Docker, opcional;
- Tesseract apenas para reconstruir o índice documental a partir dos PDFs originais.

### Instalação completa para desenvolvimento

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
python -m pytest
```

### Interface web e API

```powershell
uvicorn fiesc_pm.api:app --host 127.0.0.1 --port 8000
```

Acesse:

- interface web: `http://127.0.0.1:8000/`;
- OpenAPI: `http://127.0.0.1:8000/docs`;
- prontidão: `http://127.0.0.1:8000/ready`.

### Dashboard Streamlit

```powershell
streamlit run app/streamlit_app.py
```

Acesse `http://127.0.0.1:8501`.

### Docker

```powershell
docker build -t fiesc-prescritiva:local .
docker run --rm -p 8501:8501 fiesc-prescritiva:local
```

## Endpoints

- `GET /`: redireciona para a demonstração web.
- `GET /health`: processo ativo.
- `GET /ready`: modelo, índice documental e provedores prontos.
- `GET /demo-events`: seis cenários anonimizados e reproduzíveis.
- `GET /model-info`: versão, atributos, limiares e hashes.
- `POST /v1/recommendations`: decisão, similaridade, fontes e orientação prescritiva.

O corpo do POST utiliza um `event` de `data/demo/demo_events.json`, uma pergunta, `provider: "auto"` e `top_k: 3`. No modo automático, Gemini é usado quando `GEMINI_API_KEY` está configurada; caso contrário, a mesma chamada cai para a síntese extrativa citada.

## Variáveis de ambiente

Copie `.env.example` para `.env` somente no ambiente local.

```text
FIESC_API_KEY=
FIESC_RUNTIME_DIR=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
ENABLE_OLLAMA_FALLBACK=false
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:1.7b
```

Sem chave externa, a aplicação funciona imediatamente no modo extrativo e mantém as citações documentais. Com `GEMINI_API_KEY`, `provider: "auto"` usa Gemini e volta automaticamente para o modo extrativo se o serviço externo falhar.

### Demonstração com Gemini sem segredo no Git

A chave nunca precisa aparecer em commit, ZIP, comando de terminal ou captura de tela. Configure-a localmente por entrada oculta:

```powershell
python scripts/configure_demo_env.py
uvicorn fiesc_pm.api:app --host 127.0.0.1 --port 8000
```

O script grava somente o arquivo local `.env`, ignorado pelo Git, e não imprime o valor. Confirme a integração em `GET /ready`: o campo `gemini_configured` deve retornar `true`. Na interface, o indicador mostra `Motor online · Gemini` e cada resultado informa o provedor efetivamente utilizado.

Na Vercel ou em outro ambiente de produção, cadastre `GEMINI_API_KEY` como variável de ambiente protegida e faça um novo deploy. Para exposição fora de `localhost`, configure também `FIESC_API_KEY` e envie `X-API-Key` nas chamadas protegidas.

## Qualidade e segurança

```powershell
python -m ruff check .
python -m mypy src app scripts tests
python -m pytest
python scripts/smoke_test.py
python scripts/security_check.py
python scripts/package_release.py
python scripts/validate_release.py
docker build -t fiesc-prescritiva:test .
```

A CI repete lint, tipagem, testes, cenários ponta a ponta, verificação de segurança, geração do ZIP, validação isolada do pacote e build do contêiner.

Controles implementados:

- verificação SHA-256 antes de desserializar o modelo;
- ausência de chaves no repositório;
- bloqueio de documentos pessoais e fontes privadas no pacote;
- usuário sem privilégios no contêiner;
- cabeçalhos de segurança na publicação web;
- respostas geradas somente a partir de citações recuperadas;
- recusa quando a evidência documental é insuficiente.

## Empacotamento da entrega

```powershell
python scripts/package_release.py
python scripts/validate_release.py
```

Saída esperada:

```text
output/release/Mateus_Ferreira_Lopes_FIESC_02198_Codigo.zip
```

O ZIP inclui código, modelo compacto, índice documental, interface, testes e documentação. Não inclui base original, PDFs-fonte, documentos pessoais, chaves, ambiente virtual ou arquivos temporários.

## Reconstrução dos artefatos

Os comandos abaixo dependem das fontes privadas em `../_privado/fontes`, que não integram o repositório:

```powershell
python scripts/train_model.py
python scripts/build_knowledge.py
python scripts/build_demo_events.py
```

## Estrutura

```text
src/fiesc_pm/       domínio, ML, RAG, provedores, persistência e API
app/                dashboard Streamlit
public/             demonstração web leve
artifacts/          modelo, métricas, metadados e índice documental
data/demo/          seis amostras anonimizadas
scripts/            treinamento, validação, segurança e empacotamento
tests/              unidade, API, segurança, integração e interface
docs/               arquitetura, decisões e rastreabilidade
```

## Limitações conhecidas

- Métricas por sessões são moderadas e representam a dificuldade real de generalização entre campanhas.
- Confiança de classificação não equivale a probabilidade calibrada de falha física.
- A base não representa todas as máquinas, condições e regimes industriais.
- A seleção agrupada não contém amostras da família polia.
- A recuperação textual utiliza TF-IDF local para manter rastreabilidade e baixo consumo.
- Uso industrial exige autenticação corporativa, catálogo de ativos, monitoramento de drift, observabilidade e aprovação humana.

Consulte [Arquitetura](docs/ARQUITETURA.md), [Decisões](docs/DECISIONS.md) e [Rastreabilidade](docs/TRACEABILITY.md).
