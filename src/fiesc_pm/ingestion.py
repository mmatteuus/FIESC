from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .features import build_features
from .labels import canonicalize_fault
from .schemas import SENSOR_FIELDS

EXPECTED_COLUMNS = {"id", "created_at", "fault", *SENSOR_FIELDS}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_dataset(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["created_at"], low_memory=False)
    missing = sorted(EXPECTED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes: {missing}")
    numeric = frame.loc[:, SENSOR_FIELDS].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        bad = numeric.columns[numeric.isna().any()].tolist()
        raise ValueError(f"Valores numericos invalidos em: {bad}")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("A base contem valores infinitos")
    frame.loc[:, SENSOR_FIELDS] = numeric
    frame["canonical_fault"] = frame["fault"].map(canonicalize_fault)
    return frame


def assign_sessions(frame: pd.DataFrame, max_gap_seconds: int = 60) -> pd.DataFrame:
    ordered = frame.sort_values("created_at").copy()
    gaps = ordered["created_at"].diff().dt.total_seconds().fillna(max_gap_seconds + 1)
    label_change = ordered["fault"].astype(str).ne(ordered["fault"].astype(str).shift())
    new_session = gaps.gt(max_gap_seconds) | label_change
    ordered["session_id"] = new_session.cumsum().astype("int32")
    return ordered


def audit_dataset(frame: pd.DataFrame, source_path: Path) -> dict[str, Any]:
    feature_cols = list(SENSOR_FIELDS)
    duplicates = int(frame.duplicated(subset=feature_cols, keep=False).sum())
    counts = frame["canonical_fault"].value_counts().sort_index().to_dict()
    raw_counts = frame["fault"].value_counts().to_dict()
    return {
        "source_sha256": sha256_file(source_path),
        "rows": int(len(frame)),
        "columns": int(len(frame.columns) - 1),
        "raw_labels": int(frame["fault"].nunique()),
        "canonical_counts": {str(k): int(v) for k, v in counts.items()},
        "raw_label_counts": {str(k): int(v) for k, v in raw_counts.items()},
        "null_values": int(frame.isna().sum().sum()),
        "duplicate_feature_rows_including_all_copies": duplicates,
        "duplicate_timestamps": int(frame["created_at"].duplicated().sum()),
        "date_min": frame["created_at"].min().isoformat(),
        "date_max": frame["created_at"].max().isoformat(),
        "rpm_counts": {str(k): int(v) for k, v in frame["rpm"].value_counts().sort_index().items()},
    }


def prepare_training_data(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    with_sessions = assign_sessions(frame)
    dedup_subset = [*SENSOR_FIELDS, "canonical_fault"]
    deduplicated = with_sessions.drop_duplicates(subset=dedup_subset, keep="first").copy()
    if (deduplicated["canonical_fault"] == "unknown").any():
        unknown = sorted(
            deduplicated.loc[deduplicated["canonical_fault"] == "unknown", "fault"].unique()
        )
        raise ValueError(f"Rotulos sem mapeamento: {unknown}")
    features = build_features(deduplicated)
    labels = deduplicated["canonical_fault"].astype(str)
    groups = deduplicated["session_id"].astype("int32")
    return features, labels, groups, deduplicated
