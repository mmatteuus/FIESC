# Decisões técnicas

## D-001 — Python 3.12

Python 3.12 foi escolhido pela compatibilidade com o ecossistema de aprendizado de máquina, FastAPI e Streamlit.

## D-002 — Separação por sessões

Treino, seleção e teste usam sessões de aquisição disjuntas. O teste independente não participa da escolha do modelo nem da definição dos limiares. A divisão aleatória aparece somente como diagnóstico do risco de vazamento.

## D-003 — Abstenção antes da recomendação

O modelo de linguagem não é consultado para falha sem documento, baixa confiança, evento fora do padrão conhecido ou operação normal.

## D-004 — Provedores

Gemini é o provedor principal. Ollama permanece opcional porque sua latência local ultrapassou 60 segundos. A contingência automática é uma síntese extrativa das mesmas fontes recuperadas.

## D-005 — Privacidade

A base completa, os documentos oficiais, os anexos pessoais e os segredos permanecem fora do repositório. As amostras de demonstração não contêm os identificadores originais.

## D-006 — Integridade e exposição

O SHA-256 do artefato é verificado antes da desserialização. A API permanece aberta em desenvolvimento local; quando `FIESC_API_KEY` é definida, o endpoint de recomendação exige `X-API-Key`. Uma exposição externa também requer identidade, limitação de requisições e limite de corpo no gateway.

## D-007 — Similaridade histórica

Vizinhos não substituem o classificador. Eles sustentam a explicação operacional e geram quantidade de referências, distribuição diária, frequência média, condições observadas e contexto de RPM. O limite de proximidade usa o mesmo percentil validado para detecção de novidade.
