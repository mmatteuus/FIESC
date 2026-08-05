from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import cast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from fiesc_pm.config import get_settings
from fiesc_pm.schemas import (
    ProviderName,
    RecommendationRequest,
    RecommendationResponse,
    SensorEvent,
)
from fiesc_pm.service import RecommendationService

LOGGER = logging.getLogger(__name__)

FAULT_LABELS = {
    "bearing": "Rolamento",
    "belt": "Correia",
    "cocked_rotor": "Rotor inclinado",
    "eccentric_rotor": "Rotor excêntrico",
    "fan": "Ventilador",
    "imbalance": "Desbalanceamento",
    "misalignment": "Desalinhamento",
    "normal": "Operação normal",
    "phase_loss": "Perda de fase",
    "pulley": "Polia",
}
STATE_LABELS = {
    "operating": "Em operação",
    "motor_off": "Motor parado",
    "acceleration": "Em aceleração",
}
PROVIDER_LABELS = {
    "none": "Não consultado",
    "gemini": "Gemini",
    "ollama": "Modelo local",
    "extractive": "Síntese documental",
}
SCENARIO_LABELS = {
    "falha_documentada_rolamento": "Falha em rolamento",
    "falha_documentada_desalinhamento": "Desalinhamento",
    "sem_documento_rotor_excentrico": "Rotor excêntrico sem documento",
    "sem_documento_perda_de_fase": "Perda de fase sem documento",
    "operacao_normal": "Operação normal",
    "baixa_confianca": "Resultado inconclusivo",
}
STATUS_LABELS = {
    "supported": "Recomendação liberada",
    "unsupported_documentation": "Sem documento para recomendar",
    "low_confidence": "Revisão humana necessária",
    "normal_operation": "Operação normal",
    "llm_unavailable": "Evidência indisponível",
}

st.set_page_config(
    page_title="FIESC | Manutenção Prescritiva",
    page_icon="⚙️",
    layout="wide",
)


@st.cache_resource
def load_service() -> RecommendationService:
    return RecommendationService()


@st.cache_data
def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def confidence_chart(value: float, threshold: float) -> go.Figure:
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value * 100,
            number={"suffix": "%"},
            title={"text": "Score de confiança do modelo"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#0B6E4F"},
                "threshold": {
                    "line": {"color": "#B42318", "width": 4},
                    "value": threshold * 100,
                },
                "steps": [
                    {"range": [0, threshold * 100], "color": "#F7D7D7"},
                    {"range": [threshold * 100, 100], "color": "#CFE8DA"},
                ],
            },
        )
    ).update_layout(height=260, margin={"l": 25, "r": 25, "t": 55, "b": 10})


def analyze_event(payload: object, question: str, provider: ProviderName) -> None:
    st.session_state.pop("response", None)
    try:
        event = SensorEvent.model_validate(payload)
        request = RecommendationRequest(event=event, question=question, provider=provider)
        with st.spinner("Analisando o evento e conferindo a documentação..."):
            st.session_state["response"] = load_service().analyze(request)
    except (json.JSONDecodeError, ValueError, TypeError):
        st.error("A entrada possui campos ausentes, valores inválidos ou unidades inconsistentes.")
    except Exception:
        LOGGER.exception("Falha inesperada ao analisar evento")
        st.error("Não foi possível concluir a análise. Verifique o serviço e tente novamente.")


def show_decision(response: RecommendationResponse) -> None:
    message = STATUS_LABELS.get(response.status, response.status)
    if response.status in {"supported", "normal_operation"}:
        st.success(message)
    elif response.status in {"unsupported_documentation", "low_confidence"}:
        st.warning(message)
    else:
        st.error(message)


settings = get_settings()
demos = cast(list[dict[str, object]], load_json(settings.repo_root / "data/demo/demo_events.json"))
metrics = cast(dict[str, object], load_json(settings.metrics_path))
metadata = cast(dict[str, object], load_json(settings.metadata_path))
demo_by_name = {str(item["name"]): item for item in demos}

st.title("Manutenção prescritiva")
st.caption("Diagnóstico, histórico semelhante e recomendações apoiadas por documentação técnica.")

with st.sidebar:
    st.header("Analisar um cenário")
    selected_name = st.selectbox(
        "Exemplo",
        list(demo_by_name),
        format_func=lambda value: SCENARIO_LABELS.get(value, value),
    )
    question = st.text_input(
        "Pergunta para a recomendação",
        "Quais verificações e ações corretivas devo executar?",
        max_chars=500,
    )
    with st.expander("Configuração avançada"):
        provider_value = st.selectbox(
            "Modo de recomendação",
            ["auto", "gemini", "extractive", "ollama"],
            format_func=lambda value: {
                "auto": "Automático",
                "gemini": "Gemini",
                "extractive": "Somente documentos",
                "ollama": "Modelo local",
            }[value],
            help="O modo automático usa a melhor opção disponível e preserva as mesmas regras.",
        )
    provider = cast(ProviderName, provider_value)
    if st.button("Analisar cenário", type="primary", width="stretch"):
        analyze_event(demo_by_name[selected_name]["event"], question, provider)
    st.info("Nenhuma recomendação substitui inspeção, bloqueio e aprovação técnica.")

overview_tab, input_tab, diagnosis_tab, evidence_tab, quality_tab = st.tabs(
    [
        "Visão geral",
        "Nova análise",
        "Diagnóstico e ações",
        "Evidências",
        "Qualidade e limites",
    ]
)

response = cast(RecommendationResponse | None, st.session_state.get("response"))

with overview_tab:
    if not response:
        audit = cast(dict[str, object], metadata["source_audit"])
        first, second, third, fourth = st.columns(4)
        row_count = int(cast(int | str, audit["rows"]))
        first.metric("Medições auditadas", f"{row_count:,}".replace(",", "."))
        second.metric("Condições consolidadas", "10")
        third.metric("Famílias documentadas", "6 de 9 falhas")
        fourth.metric("Sessões de teste", str(metrics.get("test_sessions", 74)))
        st.info("Escolha um exemplo na barra lateral e clique em **Analisar cenário**.")
        st.write(
            "A decisão combina sinais dos sensores, comparação com eventos históricos e "
            "documentos técnicos. Quando a evidência é insuficiente, o sistema não recomenda."
        )
    else:
        show_decision(response)
        first, second, third, fourth = st.columns(4)
        first.metric(
            "Situação", STATE_LABELS.get(response.operating_state, response.operating_state)
        )
        second.metric(
            "Falha provável", FAULT_LABELS.get(response.predicted_fault, response.predicted_fault)
        )
        third.metric("Documento disponível", "Sim" if response.documentation_available else "Não")
        fourth.metric("Eventos semelhantes", response.similarity_summary.reference_count)
        if response.recommendation:
            st.subheader("Orientação principal")
            st.write(response.recommendation.summary)
        else:
            st.write("O sistema interrompeu o fluxo antes de emitir uma ação de manutenção.")

with input_tab:
    st.subheader("Entrada personalizada")
    st.write("Edite os valores do exemplo selecionado ou cole um evento JSON.")
    event_payload = cast(dict[str, object], demo_by_name[selected_name]["event"])
    form_tab, json_tab = st.tabs(["Formulário", "JSON"])
    with form_tab:
        editable = pd.DataFrame([event_payload])
        edited = st.data_editor(editable, hide_index=True, num_rows="fixed", width="stretch")
        if st.button("Analisar formulário", width="stretch"):
            analyze_event(edited.iloc[0].to_dict(), question, provider)
    with json_tab:
        event_json = st.text_area(
            "Evento",
            value=json.dumps(event_payload, ensure_ascii=False, indent=2),
            height=360,
        )
        if st.button("Analisar JSON", width="stretch"):
            try:
                payload = json.loads(event_json)
            except json.JSONDecodeError:
                st.session_state.pop("response", None)
                st.error("O JSON não está bem formatado.")
            else:
                analyze_event(payload, question, provider)

with diagnosis_tab:
    if not response:
        st.info("Execute uma análise para visualizar o diagnóstico.")
    else:
        for warning in response.warnings:
            st.warning(warning)
        if response.recommendation:
            st.subheader("Ações sugeridas")
            for index, action in enumerate(response.recommendation.actions, start=1):
                st.write(f"{index}. {action}")
            st.subheader("Antes de intervir")
            for check in response.recommendation.safety_checks:
                st.write(f"- {check}")

        if response.operating_state == "motor_off":
            st.info(
                "Score e novidade não se aplicam: o motor parado foi identificado por regra operacional."
            )
        else:
            chart_column, explanation_column = st.columns([1, 1.2])
            chart_column.plotly_chart(
                confidence_chart(
                    response.confidence,
                    float(cast(float | int | str, metrics["confidence_threshold"])),
                ),
                width="stretch",
            )
            with explanation_column:
                st.metric("Índice de novidade", f"{response.novelty_score:.2f}")
                st.write(
                    "O score indica segurança relativa do classificador; **não representa a "
                    "probabilidade física de a falha existir**."
                )
                st.write("Novidade acima de **1,0** bloqueia a recomendação.")

with evidence_tab:
    if not response:
        st.info("Execute uma análise para visualizar o histórico e as fontes.")
    else:
        summary = response.similarity_summary
        first, second, third = st.columns(3)
        first.metric("Referências semelhantes", summary.reference_count)
        period = "Não disponível"
        if summary.first_seen and summary.last_seen:
            period = f"{summary.first_seen:%d/%m/%Y} a {summary.last_seen:%d/%m/%Y}"
        second.metric("Período observado", period)
        third.metric("Frequência média", f"{summary.events_per_day:.1f} por dia")

        if summary.daily_counts:
            timeline = pd.DataFrame(
                sorted(summary.daily_counts.items()), columns=["Data", "Eventos semelhantes"]
            )
            timeline["Data"] = pd.to_datetime(timeline["Data"])
            st.plotly_chart(
                px.line(timeline, x="Data", y="Eventos semelhantes", markers=True).update_layout(
                    height=320
                ),
                width="stretch",
            )

        chart_left, chart_right = st.columns(2)
        if summary.condition_counts:
            condition_frame = pd.DataFrame(
                [
                    {"Condição observada": FAULT_LABELS.get(name, name), "Eventos": count}
                    for name, count in summary.condition_counts.items()
                ]
            ).sort_values("Eventos")
            chart_left.plotly_chart(
                px.bar(
                    condition_frame,
                    x="Eventos",
                    y="Condição observada",
                    orientation="h",
                    color="Eventos",
                    color_continuous_scale=["#CFE8DA", "#0B6E4F"],
                ).update_layout(height=340, coloraxis_showscale=False),
                width="stretch",
            )
        if summary.rpm_counts:
            rpm_frame = pd.DataFrame(
                [(float(rpm), count) for rpm, count in summary.rpm_counts.items()],
                columns=["RPM", "Eventos"],
            ).sort_values("RPM")
            chart_right.plotly_chart(
                px.bar(
                    rpm_frame, x="RPM", y="Eventos", color_discrete_sequence=["#0B6E4F"]
                ).update_layout(height=340),
                width="stretch",
            )

        if response.similar_cases:
            st.subheader("Casos mais próximos")
            threshold = float(cast(float | int | str, metrics["novelty_distance_threshold"]))
            cases = pd.DataFrame(
                [
                    {
                        "Condição observada": FAULT_LABELS.get(
                            case.fault_family, case.fault_family
                        ),
                        "Data": case.created_at.strftime("%d/%m/%Y %H:%M")
                        if case.created_at
                        else "-",
                        "RPM": f"{case.rpm:g}",
                        "Proximidade": f"{max(0.0, 1 - case.distance / threshold):.0%}",
                    }
                    for case in response.similar_cases
                ]
            )
            st.dataframe(cases, width="stretch", hide_index=True)

        st.subheader("Documentos consultados")
        if not response.citations:
            st.info(
                "Nenhum documento foi consultado porque uma regra de segurança interrompeu o fluxo."
            )
        else:
            for citation in response.citations:
                with st.expander(f"{citation.document} — página {citation.page}"):
                    st.write(citation.excerpt)
                    st.caption(f"Relevância do trecho: {citation.score:.0%}")

with quality_tab:
    holdout = cast(dict[str, float], metrics.get("holdout_test", {}))
    selected = str(metrics["selected_model"])
    selection = cast(dict[str, dict[str, float]], metrics["group_split"])
    if not holdout:
        holdout = selection[selected]
    first, second, third = st.columns(3)
    first.metric("Macro F1 no teste", f"{holdout['macro_f1']:.3f}")
    second.metric("Acurácia balanceada", f"{holdout['balanced_accuracy']:.3f}")
    third.metric("Sessões independentes", str(metrics.get("test_sessions", 0)))
    st.caption("O conjunto de teste não participa da escolha do modelo nem dos limiares.")

    rows = [
        {
            "Modelo": name.replace("_", " ").title(),
            "Macro F1 na seleção": values["macro_f1"],
            "Acurácia balanceada": values["balanced_accuracy"],
            "Tamanho (MB)": values.get("compressed_estimator_bytes", 0) / 1_048_576,
        }
        for name, values in selection.items()
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    random_f1 = cast(dict[str, float], metrics["random_split_diagnostic"])["macro_f1"]
    st.warning(
        f"Uma divisão aleatória alcançou macro F1 {random_f1:.3f}, mas mistura contextos "
        "semelhantes e superestima a generalização."
    )
    st.subheader("Limites da solução")
    st.write("- O score do classificador não é uma probabilidade física calibrada.")
    st.write("- Famílias sem documento são recusadas antes da geração da recomendação.")
    st.write("- Toda intervenção depende de inspeção e aprovação profissional.")
    if response:
        with st.expander("Detalhes técnicos da última análise"):
            st.json(
                {
                    "provedor": PROVIDER_LABELS.get(response.provider, response.provider),
                    "modelo": response.model_version,
                    "latência_ms": response.latency_ms,
                    "id_da_análise": response.request_id,
                }
            )
