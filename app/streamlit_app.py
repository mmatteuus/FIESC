from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import cast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.ui_localization import (
    DEFAULT_LANGUAGE,
    FIELD_GROUPS,
    LANGUAGE_OPTIONS,
    Language,
    build_event_payload,
    localized_date_format,
    localized_datetime_format,
    localized_fault_label,
    localized_field_label,
    localized_provider_label,
    localized_scenario_label,
    localized_state_label,
    localized_warning,
    recommended_question,
    translate,
)
from fiesc_pm.config import get_settings
from fiesc_pm.schemas import (
    ProviderName,
    RecommendationRequest,
    RecommendationResponse,
    SensorEvent,
)
from fiesc_pm.service import RecommendationService

LOGGER = logging.getLogger(__name__)


def current_language() -> Language:
    selected = st.session_state.get("language")
    if isinstance(selected, str) and selected in LANGUAGE_OPTIONS:
        return LANGUAGE_OPTIONS[selected]
    return DEFAULT_LANGUAGE


def clear_response_on_language_change() -> None:
    st.session_state.pop("response", None)


language = current_language()
st.set_page_config(page_title=translate("page_title", language), page_icon="⚙️", layout="wide")


@st.cache_resource
def load_service() -> RecommendationService:
    return RecommendationService()


@st.cache_data
def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def confidence_chart(value: float, threshold: float, language: Language) -> go.Figure:
    return go.Figure(go.Indicator(
        mode="gauge+number", value=value * 100, number={"suffix": "%"},
        title={"text": translate("confidence_score", language)},
        gauge={
            "axis": {"range": [0, 100]}, "bar": {"color": "#0B6E4F"},
            "threshold": {"line": {"color": "#B42318", "width": 4}, "value": threshold * 100},
            "steps": [{"range": [0, threshold * 100], "color": "#F7D7D7"}, {"range": [threshold * 100, 100], "color": "#CFE8DA"}],
        },
    )).update_layout(height=260, margin={"l": 25, "r": 25, "t": 55, "b": 10})


def analyze_event(payload: object, question: str, provider: ProviderName, language: Language) -> None:
    st.session_state.pop("response", None)
    try:
        event = SensorEvent.model_validate(payload)
        request = RecommendationRequest(
            event=event, question=recommended_question(question, language), provider=provider
        )
        with st.spinner(translate("analyzing", language)):
            st.session_state["response"] = load_service().analyze(request)
    except (json.JSONDecodeError, ValueError, TypeError):
        st.error(translate("invalid_input", language))
    except Exception:
        LOGGER.exception("Unexpected event analysis failure")
        st.error(translate("analysis_error", language))

def show_decision(response: RecommendationResponse, language: Language) -> None:
    message = translate(response.status, language)
    if response.status in {"supported", "normal_operation"}:
        st.success(message)
    elif response.status in {"unsupported_documentation", "low_confidence"}:
        st.warning(message)
    else:
        st.error(message)

def render_summary_cards(response: RecommendationResponse, language: Language) -> None:
    cards = (
        (translate("operating_state", language), localized_state_label(response.operating_state, language)),
        (translate("predicted_fault", language), localized_fault_label(response.predicted_fault, language)),
        (translate("documentation_available", language), translate("yes" if response.documentation_available else "no", language)),
        (translate("similar_events", language), str(response.similarity_summary.reference_count)),
    )
    first_row = st.columns(2)
    second_row = st.columns(2)
    for column, (label, value) in zip((*first_row, *second_row), cards, strict=True):
        with column, st.container(border=True):
            st.caption(label)
            st.markdown(f"### {value}")

def render_event_form(event_payload: dict[str, object], language: Language) -> dict[str, object]:
    edited = dict(event_payload)
    for group_key, fields in FIELD_GROUPS:
        present_fields = [field for field in fields if field in event_payload]
        if not present_fields:
            continue
        st.markdown(f"#### {translate(group_key, language)}")
        columns = st.columns(2)
        for index, field in enumerate(present_fields):
            value = event_payload[field]
            with columns[index % 2]:
                if field == "id":
                    edited[field] = st.text_input(localized_field_label(field, language), value="" if value is None else str(value), key=f"field_{field}") or None
                elif field == "created_at":
                    edited[field] = value
                    st.text_input(localized_field_label(field, language), value="" if value is None else str(value), disabled=True, key=f"field_{field}")
                else:
                    formatted = "%.6g" if field != "rpm" else "%.1f"
                    edited[field] = st.number_input(localized_field_label(field, language), value=float(cast(float | int, value)), format=formatted, key=f"field_{field}")
    return build_event_payload(event_payload, edited)

settings = get_settings()
demos = cast(list[dict[str, object]], load_json(settings.repo_root / "data/demo/demo_events.json"))
metrics = cast(dict[str, object], load_json(settings.metrics_path))
metadata = cast(dict[str, object], load_json(settings.metadata_path))
demo_by_name = {str(item["name"]): item for item in demos}

with st.sidebar:
    language_name = st.selectbox(
        translate("language", language), list(LANGUAGE_OPTIONS),
        index=list(LANGUAGE_OPTIONS.values()).index(language), key="language",
        on_change=clear_response_on_language_change,
    )
    language = LANGUAGE_OPTIONS[str(language_name)]
    st.header(translate("sidebar_title", language))
    selected_name = st.selectbox(
        translate("example", language), list(demo_by_name),
        format_func=lambda value: localized_scenario_label(value, language),
        key=f"scenario_{language}",
    )
    question = st.text_input(translate("question", language), value=translate("default_question", language), max_chars=500, key=f"question_{language}")
    with st.expander(translate("advanced", language)):
        provider_value = st.selectbox(translate("recommendation_mode", language), ["auto", "gemini", "extractive", "ollama"], format_func=lambda value: translate(f"mode_{value}", language), help=translate("mode_help", language))
    provider = cast(ProviderName, provider_value)
    if st.button(translate("analyze_scenario", language), type="primary", width="stretch"):
        analyze_event(demo_by_name[selected_name]["event"], question, provider, language)
    st.info(translate("safety_notice", language))

st.title(translate("title", language))
st.caption(translate("subtitle", language))
overview_tab, input_tab, diagnosis_tab, evidence_tab, quality_tab = st.tabs([
    translate("overview", language), translate("new_analysis", language), translate("diagnosis_actions", language),
    translate("evidence", language), translate("quality_limits", language),
])
response = cast(RecommendationResponse | None, st.session_state.get("response"))

with overview_tab:
    if not response:
        audit = cast(dict[str, object], metadata["source_audit"])
        first, second, third, fourth = st.columns(4)
        row_count = int(cast(int | str, audit["rows"]))
        first.metric(translate("measurements_audited", language), f"{row_count:,}".replace(",", "."))
        second.metric(translate("consolidated_conditions", language), "10")
        third.metric(translate("documented_families", language), "6 / 9")
        fourth.metric(translate("test_sessions", language), str(metrics.get("test_sessions", 74)))
        st.info(translate("choose_scenario", language))
        st.write(translate("decision_explanation", language))
    else:
        show_decision(response, language)
        render_summary_cards(response, language)
        if response.recommendation:
            st.subheader(translate("main_guidance", language))
            st.write(response.recommendation.summary)
        else:
            st.write(translate("flow_stopped", language))

with input_tab:
    st.subheader(translate("custom_input", language))
    st.write(translate("custom_input_help", language))
    event_payload = cast(dict[str, object], demo_by_name[selected_name]["event"])
    form_tab, json_tab = st.tabs([translate("event_data", language), translate("technical_json", language)])
    with form_tab:
        edited_payload = render_event_form(event_payload, language)
        if st.button(translate("analyze_form", language), width="stretch"):
            analyze_event(edited_payload, question, provider, language)
    with json_tab:
        st.caption(translate("json_help", language))
        event_json = st.text_area(translate("event", language), value=json.dumps(event_payload, ensure_ascii=False, indent=2), height=360)
        if st.button(translate("analyze_json", language), width="stretch"):
            try:
                payload = json.loads(event_json)
            except json.JSONDecodeError:
                st.session_state.pop("response", None)
                st.error(translate("invalid_json", language))
            else:
                analyze_event(payload, question, provider, language)

with diagnosis_tab:
    if not response:
        st.info(translate("run_analysis_diagnosis", language))
    else:
        for warning in response.warnings:
            st.warning(localized_warning(warning, language))
        if response.recommendation:
            st.subheader(translate("suggested_actions", language))
            for index, action in enumerate(response.recommendation.actions, start=1):
                st.write(f"{index}. {action}")
            st.subheader(translate("safety_checks", language))
            for check in response.recommendation.safety_checks:
                st.write(f"- {check}")
        if response.operating_state == "motor_off":
            st.info(translate("motor_off_note", language))
        else:
            chart_column, explanation_column = st.columns([1, 1.2])
            chart_column.plotly_chart(confidence_chart(response.confidence, float(cast(float | int | str, metrics["confidence_threshold"])), language), width="stretch")
            with explanation_column:
                st.metric(translate("novelty_index", language), f"{response.novelty_score:.2f}")
                st.write(translate("confidence_explanation", language))
                st.write(translate("novelty_limit", language))

with evidence_tab:
    if not response:
        st.info(translate("run_analysis_evidence", language))
    else:
        summary = response.similarity_summary
        first, second, third = st.columns(3)
        first.metric(translate("similar_references", language), summary.reference_count)
        period = translate("not_available", language)
        if summary.first_seen and summary.last_seen:
            date_format = localized_date_format(language)
            period = f"{summary.first_seen:{date_format}} - {summary.last_seen:{date_format}}"
        second.metric(translate("observed_period", language), period)
        third.metric(translate("average_frequency", language), f"{summary.events_per_day:.1f} {translate('per_day', language)}")
        if summary.daily_counts:
            timeline = pd.DataFrame(sorted(summary.daily_counts.items()), columns=[translate("date", language), translate("similar_events", language)])
            timeline[translate("date", language)] = pd.to_datetime(timeline[translate("date", language)])
            st.plotly_chart(px.line(timeline, x=translate("date", language), y=translate("similar_events", language), markers=True).update_layout(height=320), width="stretch")
        chart_left, chart_right = st.columns(2)
        if summary.condition_counts:
            condition_frame = pd.DataFrame([{translate("observed_condition", language): localized_fault_label(name, language), translate("events", language): count} for name, count in summary.condition_counts.items()]).sort_values(translate("events", language))
            chart_left.plotly_chart(px.bar(condition_frame, x=translate("events", language), y=translate("observed_condition", language), orientation="h", color=translate("events", language), color_continuous_scale=["#CFE8DA", "#0B6E4F"]).update_layout(height=340, coloraxis_showscale=False), width="stretch")
        if summary.rpm_counts:
            rpm_frame = pd.DataFrame([(float(rpm), count) for rpm, count in summary.rpm_counts.items()], columns=["RPM", translate("events", language)]).sort_values("RPM")
            chart_right.plotly_chart(px.bar(rpm_frame, x="RPM", y=translate("events", language), color_discrete_sequence=["#0B6E4F"]).update_layout(height=340), width="stretch")
        if response.similar_cases:
            st.subheader(translate("closest_cases", language))
            threshold = float(cast(float | int | str, metrics["novelty_distance_threshold"]))
            datetime_format = localized_datetime_format(language)
            cases = pd.DataFrame([{translate("observed_condition", language): localized_fault_label(case.fault_family, language), translate("date", language): case.created_at.strftime(datetime_format) if case.created_at else "-", "RPM": f"{case.rpm:g}", translate("proximity", language): f"{max(0.0, 1 - case.distance / threshold):.0%}"} for case in response.similar_cases])
            st.dataframe(cases, width="stretch", hide_index=True)
        st.subheader(translate("consulted_documents", language))
        if not response.citations:
            st.info(translate("no_documents", language))
        else:
            for citation in response.citations:
                with st.expander(f"{citation.document} — {translate('page', language)} {citation.page}"):
                    st.write(citation.excerpt)
                    st.caption(f"{translate('excerpt_relevance', language)}: {citation.score:.0%}")

with quality_tab:
    holdout = cast(dict[str, float], metrics.get("holdout_test", {}))
    selected = str(metrics["selected_model"])
    selection = cast(dict[str, dict[str, float]], metrics["group_split"])
    if not holdout:
        holdout = selection[selected]
    first, second, third = st.columns(3)
    first.metric(translate("macro_f1", language), f"{holdout['macro_f1']:.3f}")
    second.metric(translate("balanced_accuracy", language), f"{holdout['balanced_accuracy']:.3f}")
    third.metric(translate("independent_sessions", language), str(metrics.get("test_sessions", 0)))
    st.caption(translate("test_caption", language))
    rows = [{translate("model", language): name.replace("_", " ").title(), translate("selection_macro_f1", language): values["macro_f1"], translate("balanced_accuracy", language): values["balanced_accuracy"], translate("size_mb", language): values.get("compressed_estimator_bytes", 0) / 1_048_576} for name, values in selection.items()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    random_f1 = cast(dict[str, float], metrics["random_split_diagnostic"])["macro_f1"]
    st.warning(translate("random_split_warning", language, value=random_f1))
    st.subheader(translate("solution_limits", language))
    st.write(f"- {translate('limit_score', language)}")
    st.write(f"- {translate('limit_docs', language)}")
    st.write(f"- {translate('limit_human', language)}")
    if response:
        with st.expander(translate("technical_details", language)):
            st.json({translate("provider", language): localized_provider_label(response.provider, language), translate("model", language): response.model_version, translate("latency_ms", language): response.latency_ms, translate("analysis_id", language): response.request_id})
