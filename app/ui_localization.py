from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

Language = Literal["pt-BR", "en"]
DEFAULT_LANGUAGE: Language = "pt-BR"
LANGUAGE_OPTIONS: dict[str, Language] = {"Português (Brasil)": "pt-BR", "English": "en"}

FAULT_KEYS = (
    "bearing", "belt", "cocked_rotor", "eccentric_rotor", "fan", "imbalance",
    "misalignment", "normal", "phase_loss", "pulley",
)
STATE_KEYS = ("operating", "motor_off", "acceleration")
STATUS_KEYS = (
    "supported", "unsupported_documentation", "low_confidence",
    "normal_operation", "llm_unavailable",
)
MODE_KEYS = ("auto", "gemini", "extractive", "ollama")
PROVIDER_KEYS = {"none": "provider_none", "gemini": "provider_gemini", "ollama": "provider_ollama", "extractive": "provider_extractive"}
SCENARIO_KEYS = {
    "falha_documentada_rolamento": "scenario_bearing",
    "falha_documentada_desalinhamento": "scenario_misalignment",
    "sem_documento_rotor_excentrico": "scenario_eccentric",
    "sem_documento_perda_de_fase": "scenario_phase_loss",
    "operacao_normal": "scenario_normal",
    "baixa_confianca": "scenario_low_confidence",
}
WARNING_KEYS = {
    "Motor parado: estado definido por regra operacional; o score do modelo não se aplica.": "warning_motor_off",
    "Inspecao humana necessaria antes de classificar a falha.": "warning_human_inspection",
    "Nao existe documento cadastrado para esta familia; registrar nova documentacao.": "warning_no_document",
    "Documento registrado, mas nenhuma evidencia foi recuperada.": "warning_no_evidence",
    "Serviço de linguagem indisponível; síntese documental utilizada.": "warning_llm_fallback",
}
FIELD_KEYS = (
    "id", "created_at", "z_rms_velocity_in_s", "z_rms_velocity_mm_s",
    "temperature_f", "temperature_c", "x_rms_velocity_in_s",
    "x_rms_velocity_mm_s", "z_peak_acceleration_g", "x_peak_acceleration_g",
    "z_peak_vel_comp_freq_hz", "x_peak_vel_comp_freq_hz",
    "z_rms_acceleration_g", "x_rms_acceleration_g", "z_kurtosis", "x_kurtosis",
    "z_crest_factor", "x_crest_factor", "z_peak_velocity_in_s",
    "z_peak_velocity_mm_s", "x_peak_velocity_in_s", "x_peak_velocity_mm_s",
    "z_high_freq_rms_accel_g", "x_high_freq_rms_accel_g", "rpm",
)

TRANSLATIONS: dict[Language, dict[str, str]] = {
    "pt-BR": {
        "page_title": "FIESC | Manutenção prescritiva", "title": "Manutenção prescritiva",
        "subtitle": "Diagnóstico, eventos semelhantes e recomendações apoiadas por documentação técnica.",
        "language": "Idioma da interface", "language_note": "Trechos técnicos das fontes podem permanecer no idioma original.",
        "sidebar_title": "Analisar um cenário", "example": "Exemplo",
        "question": "Pergunta para a recomendação", "default_question": "Quais verificações e ações corretivas devo executar?",
        "advanced": "Configuração avançada", "recommendation_mode": "Modo de recomendação",
        "mode_auto": "Automático", "mode_gemini": "Gemini", "mode_extractive": "Somente documentos", "mode_ollama": "Modelo local",
        "mode_help": "O modo automático usa a melhor opção disponível e preserva as mesmas regras de segurança.",
        "analyze_scenario": "Analisar cenário", "safety_notice": "Nenhuma recomendação substitui inspeção, bloqueio e aprovação técnica.",
        "overview": "Visão geral", "new_analysis": "Nova análise", "diagnosis_actions": "Diagnóstico e ações",
        "evidence": "Evidências", "quality_limits": "Qualidade e limites", "measurements_audited": "Medições auditadas",
        "consolidated_conditions": "Condições consolidadas", "documented_families": "Famílias documentadas", "test_sessions": "Sessões de teste",
        "choose_scenario": "Escolha um exemplo na barra lateral e clique em **Analisar cenário**.",
        "decision_explanation": "A decisão combina sinais dos sensores, comparação com eventos históricos e documentos técnicos. Quando a evidência é insuficiente, o sistema não recomenda.",
        "operating_state": "Situação", "predicted_fault": "Falha provável", "documentation_available": "Documento disponível",
        "similar_events": "Eventos semelhantes", "yes": "Sim", "no": "Não", "main_guidance": "Orientação principal",
        "flow_stopped": "O sistema interrompeu o fluxo antes de emitir uma ação de manutenção.",
        "custom_input": "Entrada personalizada", "custom_input_help": "Edite os valores do exemplo selecionado ou cole um evento JSON.",
        "event_data": "Dados do evento", "technical_json": "JSON técnico", "json_help": "O JSON utiliza os nomes técnicos internos exigidos pela API e pelo schema.",
        "analyze_form": "Analisar formulário", "analyze_json": "Analisar JSON", "event": "Evento",
        "invalid_json": "O JSON não está bem formatado.", "analyzing": "Analisando o evento e conferindo a documentação...",
        "invalid_input": "A entrada possui campos ausentes, valores inválidos ou unidades inconsistentes.",
        "analysis_error": "Não foi possível concluir a análise. Verifique o serviço e tente novamente.",
        "run_analysis_diagnosis": "Execute uma análise para visualizar o diagnóstico.", "suggested_actions": "Ações sugeridas",
        "safety_checks": "Verificações de segurança", "motor_off_note": "Score e novidade não se aplicam: o motor desligado foi identificado por regra operacional.",
        "confidence_score": "Score de confiança do modelo", "novelty_index": "Índice de novidade",
        "confidence_explanation": "O score indica a segurança relativa do classificador; **não representa a probabilidade física de a falha existir**.",
        "novelty_limit": "Novidade acima de **1,0** bloqueia a recomendação.", "run_analysis_evidence": "Execute uma análise para visualizar o histórico e as fontes.",
        "similar_references": "Referências semelhantes", "observed_period": "Período observado", "average_frequency": "Frequência média",
        "not_available": "Não disponível", "per_day": "por dia", "date": "Data", "observed_condition": "Condição observada", "events": "Eventos",
        "closest_cases": "Casos mais próximos", "proximity": "Proximidade", "consulted_documents": "Documentos consultados",
        "no_documents": "Nenhum documento foi consultado porque uma regra de segurança interrompeu o fluxo.", "page": "página",
        "excerpt_relevance": "Relevância do trecho",         "macro_f1": "Macro F1 no teste", "balanced_accuracy": "Acurácia balanceada",
        "independent_sessions": "Sessões no teste independente", "test_caption": "O conjunto de teste não participa da escolha do modelo nem dos limiares.",
        "model": "Modelo", "selection_macro_f1": "Macro F1 na seleção", "size_mb": "Tamanho (MB)",
        "random_split_warning": "Uma divisão aleatória alcançou macro F1 {value:.3f}, mas mistura contextos semelhantes e superestima a generalização.",
        "solution_limits": "Limites da solução", "limit_score": "O score do classificador não é uma probabilidade física calibrada.",
        "limit_docs": "Famílias sem documento são recusadas antes da geração da recomendação.",
        "limit_human": "Toda intervenção depende de inspeção e aprovação profissional.", "technical_details": "Detalhes técnicos da última análise",
        "provider": "provedor", "latency_ms": "latência_ms", "analysis_id": "id_da_análise",
        "identification_operation": "Identificação e operação", "vibration_velocity": "Velocidade de vibração",
        "acceleration": "Aceleração", "signal_characteristics": "Características do sinal", "temperature": "Temperatura",
        "supported": "Recomendação liberada", "unsupported_documentation": "Sem documentação para recomendar",
        "low_confidence": "Revisão humana necessária", "normal_operation": "Operação normal", "llm_unavailable": "Evidência indisponível",
        "scenario_bearing": "Falha em rolamento", "scenario_misalignment": "Desalinhamento", "scenario_eccentric": "Rotor excêntrico — sem documento",
        "scenario_phase_loss": "Perda de fase — sem documento", "scenario_normal": "Operação normal", "scenario_low_confidence": "Resultado inconclusivo",
        "provider_none": "Não consultado", "provider_gemini": "Gemini", "provider_ollama": "Modelo local", "provider_extractive": "Síntese documental",
        "warning_motor_off": "Motor parado: estado definido por regra operacional; o score do modelo não se aplica.",
        "warning_human_inspection": "Inspeção humana necessária antes de classificar a falha.",
        "warning_no_document": "Não existe documento cadastrado para esta família; registrar nova documentação.",
        "warning_no_evidence": "Documento registrado, mas nenhuma evidência foi recuperada.",
        "warning_llm_fallback": "Serviço de linguagem indisponível; síntese documental utilizada."
    },
    "en": {
        "page_title": "FIESC | Prescriptive maintenance", "title": "Prescriptive maintenance",
        "subtitle": "Diagnosis, similar events, and recommendations supported by technical documentation.",
        "language": "Interface language", "language_note": "Technical source excerpts may remain in their original language.",
        "sidebar_title": "Analyze a scenario", "example": "Example",
        "question": "Recommendation question", "default_question": "Which checks and corrective actions should I perform?",
        "advanced": "Advanced settings", "recommendation_mode": "Recommendation mode", "mode_auto": "Automatic",
        "mode_gemini": "Gemini", "mode_extractive": "Documents only", "mode_ollama": "Local model",
        "mode_help": "Automatic mode uses the best available option while preserving the same safety rules.",
        "analyze_scenario": "Analyze scenario", "safety_notice": "No recommendation replaces inspection, lockout, and technical approval.",
        "overview": "Overview", "new_analysis": "New analysis", "diagnosis_actions": "Diagnosis and actions", "evidence": "Evidence",
        "quality_limits": "Quality and limitations", "measurements_audited": "Audited measurements", "consolidated_conditions": "Consolidated conditions",
        "documented_families": "Documented families", "test_sessions": "Test sessions", "choose_scenario": "Choose an example in the sidebar and click **Analyze scenario**.",
        "decision_explanation": "The decision combines sensor signals, comparison with historical events, and technical documents. When evidence is insufficient, the system does not recommend an action.",
        "operating_state": "Operating state", "predicted_fault": "Predicted fault", "documentation_available": "Documentation available",
        "similar_events": "Similar events", "yes": "Yes", "no": "No", "main_guidance": "Main guidance",
        "flow_stopped": "The system stopped the flow before issuing a maintenance action.", "custom_input": "Custom input",
        "custom_input_help": "Edit the selected example values or paste a JSON event.", "event_data": "Event data", "technical_json": "Technical JSON",
        "json_help": "JSON uses the internal technical names required by the API and schema.", "analyze_form": "Analyze form", "analyze_json": "Analyze JSON",
        "event": "Event", "invalid_json": "The JSON is not well formatted.", "analyzing": "Analyzing the event and checking the documentation...",
        "invalid_input": "The input contains missing fields, invalid values, or inconsistent units.", "analysis_error": "The analysis could not be completed. Check the service and try again.",
        "run_analysis_diagnosis": "Run an analysis to view the diagnosis.", "suggested_actions": "Suggested actions", "safety_checks": "Safety checks",
        "motor_off_note": "Confidence and novelty do not apply: motor off was identified by an operational rule.", "confidence_score": "Model confidence score",
        "novelty_index": "Novelty index", "confidence_explanation": "The score indicates the classifier's relative confidence; it **does not represent the physical probability that the fault exists**.",
        "novelty_limit": "Novelty above **1.0** blocks the recommendation.", "run_analysis_evidence": "Run an analysis to view history and sources.",
        "similar_references": "Similar references", "observed_period": "Observed period", "average_frequency": "Average frequency", "not_available": "Not available",
        "per_day": "per day", "date": "Date", "observed_condition": "Observed condition", "events": "Events", "closest_cases": "Closest cases",
        "proximity": "Proximity", "consulted_documents": "Consulted documents", "no_documents": "No document was consulted because a safety rule stopped the flow.",
        "page": "page", "excerpt_relevance": "Excerpt relevance",         "macro_f1": "Test macro F1", "balanced_accuracy": "Balanced accuracy",
        "independent_sessions": "Sessions in the independent test set", "test_caption": "The test set does not participate in model or threshold selection.", "model": "Model",
        "selection_macro_f1": "Selection macro F1", "size_mb": "Size (MB)", "random_split_warning": "A random split reached macro F1 {value:.3f}, but mixes similar contexts and overestimates generalization.",
        "solution_limits": "Solution limitations", "limit_score": "The classifier score is not a calibrated physical probability.",
        "limit_docs": "Families without documentation are rejected before recommendation generation.", "limit_human": "Every intervention requires inspection and professional approval.",
        "technical_details": "Latest analysis technical details", "provider": "provider", "latency_ms": "latency_ms", "analysis_id": "analysis_id",
        "identification_operation": "Identification and operation", "vibration_velocity": "Vibration velocity", "acceleration": "Acceleration",
        "signal_characteristics": "Signal characteristics", "temperature": "Temperature", "supported": "Recommendation available",
        "unsupported_documentation": "No documentation available for recommendation", "low_confidence": "Human review required",
        "normal_operation": "Normal operation", "llm_unavailable": "Evidence unavailable", "scenario_bearing": "Bearing fault",
        "scenario_misalignment": "Misalignment", "scenario_eccentric": "Eccentric rotor — no documentation", "scenario_phase_loss": "Phase loss — no documentation",
        "scenario_normal": "Normal operation", "scenario_low_confidence": "Inconclusive result", "provider_none": "Not consulted", "provider_gemini": "Gemini",
        "provider_ollama": "Local model", "provider_extractive": "Document synthesis",
        "warning_motor_off": "Motor stopped: state defined by operational rule; the model score does not apply.",
        "warning_human_inspection": "Human inspection is required before classifying the fault.",
        "warning_no_document": "No document is registered for this family; register new documentation.",
        "warning_no_evidence": "A document exists, but no evidence was retrieved.",
        "warning_llm_fallback": "Language service unavailable; document synthesis used."
    }
}

FAULT_LABELS: dict[Language, dict[str, str]] = {
    "pt-BR": {"bearing": "Rolamento", "belt": "Correia", "cocked_rotor": "Rotor inclinado", "eccentric_rotor": "Rotor excêntrico", "fan": "Ventilador", "imbalance": "Desbalanceamento", "misalignment": "Desalinhamento", "normal": "Operação normal", "phase_loss": "Perda de fase", "pulley": "Polia"},
    "en": {"bearing": "Bearing", "belt": "Belt", "cocked_rotor": "Cocked rotor", "eccentric_rotor": "Eccentric rotor", "fan": "Fan", "imbalance": "Imbalance", "misalignment": "Misalignment", "normal": "Normal operation", "phase_loss": "Phase loss", "pulley": "Pulley"}
}
STATE_LABELS: dict[Language, dict[str, str]] = {
    "pt-BR": {"operating": "Em operação", "motor_off": "Motor desligado", "acceleration": "Em aceleração"},
    "en": {"operating": "Operating", "motor_off": "Motor off", "acceleration": "Acceleration"}
}
FIELD_LABELS: dict[Language, dict[str, str]] = {
    "pt-BR": {
        "id": "Identificador", "created_at": "Data e hora", "z_rms_velocity_in_s": "Velocidade RMS no eixo Z (pol/s)", "z_rms_velocity_mm_s": "Velocidade RMS no eixo Z (mm/s)",
        "temperature_f": "Temperatura (°F)", "temperature_c": "Temperatura (°C)", "x_rms_velocity_in_s": "Velocidade RMS no eixo X (pol/s)", "x_rms_velocity_mm_s": "Velocidade RMS no eixo X (mm/s)",
        "z_peak_acceleration_g": "Aceleração de pico no eixo Z (g)", "x_peak_acceleration_g": "Aceleração de pico no eixo X (g)", "z_peak_vel_comp_freq_hz": "Frequência da componente de pico no eixo Z (Hz)",
        "x_peak_vel_comp_freq_hz": "Frequência da componente de pico no eixo X (Hz)", "z_rms_acceleration_g": "Aceleração RMS no eixo Z (g)", "x_rms_acceleration_g": "Aceleração RMS no eixo X (g)",
        "z_kurtosis": "Curtose no eixo Z", "x_kurtosis": "Curtose no eixo X", "z_crest_factor": "Fator de crista no eixo Z", "x_crest_factor": "Fator de crista no eixo X",
        "z_peak_velocity_in_s": "Velocidade de pico no eixo Z (pol/s)", "z_peak_velocity_mm_s": "Velocidade de pico no eixo Z (mm/s)", "x_peak_velocity_in_s": "Velocidade de pico no eixo X (pol/s)",
        "x_peak_velocity_mm_s": "Velocidade de pico no eixo X (mm/s)", "z_high_freq_rms_accel_g": "Aceleração RMS de alta frequência no eixo Z (g)", "x_high_freq_rms_accel_g": "Aceleração RMS de alta frequência no eixo X (g)", "rpm": "Rotação (RPM)"
    },
    "en": {
        "id": "Identifier", "created_at": "Date and time", "z_rms_velocity_in_s": "Z-axis RMS velocity (in/s)", "z_rms_velocity_mm_s": "Z-axis RMS velocity (mm/s)",
        "temperature_f": "Temperature (°F)", "temperature_c": "Temperature (°C)", "x_rms_velocity_in_s": "X-axis RMS velocity (in/s)", "x_rms_velocity_mm_s": "X-axis RMS velocity (mm/s)",
        "z_peak_acceleration_g": "Z-axis peak acceleration (g)", "x_peak_acceleration_g": "X-axis peak acceleration (g)", "z_peak_vel_comp_freq_hz": "Z-axis peak component frequency (Hz)",
        "x_peak_vel_comp_freq_hz": "X-axis peak component frequency (Hz)", "z_rms_acceleration_g": "Z-axis RMS acceleration (g)", "x_rms_acceleration_g": "X-axis RMS acceleration (g)",
        "z_kurtosis": "Z-axis kurtosis", "x_kurtosis": "X-axis kurtosis", "z_crest_factor": "Z-axis crest factor", "x_crest_factor": "X-axis crest factor",
        "z_peak_velocity_in_s": "Z-axis peak velocity (in/s)", "z_peak_velocity_mm_s": "Z-axis peak velocity (mm/s)", "x_peak_velocity_in_s": "X-axis peak velocity (in/s)",
        "x_peak_velocity_mm_s": "X-axis peak velocity (mm/s)", "z_high_freq_rms_accel_g": "Z-axis high-frequency RMS acceleration (g)", "x_high_freq_rms_accel_g": "X-axis high-frequency RMS acceleration (g)", "rpm": "Speed (RPM)"
    }
}
FIELD_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("identification_operation", ("id", "created_at", "rpm")),
    ("vibration_velocity", ("z_rms_velocity_in_s", "z_rms_velocity_mm_s", "x_rms_velocity_in_s", "x_rms_velocity_mm_s", "z_peak_velocity_in_s", "z_peak_velocity_mm_s", "x_peak_velocity_in_s", "x_peak_velocity_mm_s")),
    ("acceleration", ("z_peak_acceleration_g", "x_peak_acceleration_g", "z_rms_acceleration_g", "x_rms_acceleration_g", "z_high_freq_rms_accel_g", "x_high_freq_rms_accel_g")),
    ("signal_characteristics", ("z_peak_vel_comp_freq_hz", "x_peak_vel_comp_freq_hz", "z_kurtosis", "x_kurtosis", "z_crest_factor", "x_crest_factor")),
    ("temperature", ("temperature_c", "temperature_f"))
)


def translate(key: str, language: Language, **values: object) -> str:
    text = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE]).get(key, key)
    return text.format(**values) if values else text


def localized_fault_label(fault: str, language: Language) -> str:
    return FAULT_LABELS[language].get(fault, fault)


def localized_state_label(state: str, language: Language) -> str:
    return STATE_LABELS[language].get(state, state)


def localized_field_label(field: str, language: Language) -> str:
    return FIELD_LABELS[language].get(field, field)


def localized_provider_label(provider: str, language: Language) -> str:
    key = PROVIDER_KEYS.get(provider, "provider_none")
    return translate(key, language)


def localized_scenario_label(scenario: str, language: Language) -> str:
    key = SCENARIO_KEYS.get(scenario)
    return translate(key, language) if key else scenario


def localized_warning(warning: str, language: Language) -> str:
    key = WARNING_KEYS.get(warning)
    return translate(key, language) if key else warning


def localized_date_format(language: Language) -> str:
    return "%m/%d/%Y" if language == "en" else "%d/%m/%Y"


def localized_datetime_format(language: Language) -> str:
    return "%m/%d/%Y %H:%M" if language == "en" else "%d/%m/%Y %H:%M"


def localized_integer_format(value: int, language: Language) -> str:
    digits = f"{value:,}"
    return digits if language == "en" else digits.replace(",", ".")


def preserve_technical_keys(original: Mapping[str, object], edited: Mapping[str, object]) -> dict[str, object]:
    return {key: edited.get(key, value) for key, value in original.items()}


def build_event_payload(original: Mapping[str, object], edited: Mapping[str, object]) -> dict[str, object]:
    return preserve_technical_keys(original, edited)


MAX_QUESTION_LENGTH = 500
_ENGLISH_DIRECTIVE = "\nAnswer in English."


def recommended_question(question: str, language: Language) -> str:
    if language != "en" or "in english" in question.lower():
        return question
    return f"{question[: MAX_QUESTION_LENGTH - len(_ENGLISH_DIRECTIVE)]}{_ENGLISH_DIRECTIVE}"
