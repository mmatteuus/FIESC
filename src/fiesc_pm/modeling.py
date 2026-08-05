from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import tempfile
import time
from dataclasses import dataclass
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler

from .features import MODEL_FEATURES

RANDOM_STATE = 20260804


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass
class ModelBundle:
    estimator: Any
    feature_names: list[str]
    class_labels: list[str]
    confidence_threshold: float
    novelty_distance_threshold: float
    neighbor_scaler: RobustScaler
    neighbor_index: NearestNeighbors
    neighbor_metadata: list[dict[str, Any]]
    occurrence_counts: dict[str, int]
    version: str


def _candidates() -> dict[str, Pipeline]:
    return {
        "dummy": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("model", DummyClassifier(strategy="prior", random_state=RANDOM_STATE)),
            ]
        ),
        "logistic_regression": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=500,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=100,
                        max_depth=18,
                        min_samples_leaf=3,
                        class_weight="balanced_subsample",
                        n_jobs=2,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        max_iter=120,
                        learning_rate=0.08,
                        max_leaf_nodes=31,
                        l2_regularization=0.2,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def _limit_training_rows(
    x: pd.DataFrame, y: pd.Series, groups: pd.Series, limit: int = 80_000
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    if len(x) <= limit:
        return x, y, groups
    indexes: list[int] = []
    per_class = max(1, limit // y.nunique())
    rng = np.random.default_rng(RANDOM_STATE)
    for label in sorted(y.unique()):
        candidates = np.flatnonzero(y.to_numpy() == label)
        take = min(per_class, len(candidates))
        indexes.extend(rng.choice(candidates, size=take, replace=False).tolist())
    indexes = sorted(indexes)
    return x.iloc[indexes], y.iloc[indexes], groups.iloc[indexes]


def _metrics(y_true: pd.Series, y_pred: np.ndarray, labels: list[str]) -> dict[str, Any]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(
            recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
        "macro_f1": float(
            f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
        "classification_report": classification_report(
            y_true, y_pred, labels=labels, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "labels": labels,
    }


def _compressed_estimator_size(estimator: Pipeline) -> int:
    handle, temporary = tempfile.mkstemp(suffix=".joblib")
    os.close(handle)
    try:
        joblib.dump(estimator, temporary, compress=3)
        return Path(temporary).stat().st_size
    finally:
        Path(temporary).unlink(missing_ok=True)


def train_models(
    features: pd.DataFrame,
    labels: pd.Series,
    groups: pd.Series,
    source_rows: pd.DataFrame,
    full_occurrence_counts: dict[str, int],
) -> tuple[ModelBundle, dict[str, Any]]:
    outer_splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    development_idx, test_idx = next(outer_splitter.split(features, labels, groups=groups))
    inner_splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE + 1)
    relative_train_idx, relative_valid_idx = next(
        inner_splitter.split(
            features.iloc[development_idx],
            labels.iloc[development_idx],
            groups=groups.iloc[development_idx],
        )
    )
    train_idx = development_idx[relative_train_idx]
    valid_idx = development_idx[relative_valid_idx]
    train_group_ids = set(groups.iloc[train_idx])
    valid_group_ids = set(groups.iloc[valid_idx])
    test_group_ids = set(groups.iloc[test_idx])
    if (
        train_group_ids.intersection(valid_group_ids)
        or train_group_ids.intersection(test_group_ids)
        or valid_group_ids.intersection(test_group_ids)
    ):
        raise RuntimeError("Vazamento de sessao detectado")

    x_train, y_train, train_groups = _limit_training_rows(
        features.iloc[train_idx], labels.iloc[train_idx], groups.iloc[train_idx]
    )
    x_valid = features.iloc[valid_idx]
    y_valid = labels.iloc[valid_idx]
    x_test = features.iloc[test_idx]
    y_test = labels.iloc[test_idx]
    label_order = sorted(labels.unique().tolist())
    candidate_results: dict[str, Any] = {}
    fitted: dict[str, Pipeline] = {}

    for name, pipeline in _candidates().items():
        started = time.perf_counter()
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_valid)
        result = _metrics(y_valid, predictions, label_order)
        result["fit_seconds"] = round(time.perf_counter() - started, 3)
        result["compressed_estimator_bytes"] = _compressed_estimator_size(pipeline)
        result["train_rows"] = int(len(x_train))
        result["validation_rows"] = int(len(x_valid))
        candidate_results[name] = result
        fitted[name] = pipeline

    non_dummy = [name for name in candidate_results if name != "dummy"]
    best_macro_f1 = max(candidate_results[name]["macro_f1"] for name in non_dummy)
    compact_candidates = [
        name
        for name in non_dummy
        if candidate_results[name]["compressed_estimator_bytes"] <= 3_000_000
        and candidate_results[name]["macro_f1"] >= best_macro_f1 - 0.06
    ]
    selection_pool = compact_candidates or non_dummy
    ranked = sorted(
        selection_pool,
        key=lambda name: (
            candidate_results[name]["macro_f1"],
            candidate_results[name]["balanced_accuracy"],
            -candidate_results[name]["compressed_estimator_bytes"],
        ),
        reverse=True,
    )
    best_name = ranked[0]
    best = fitted[best_name]
    holdout_metrics = _metrics(y_test, best.predict(x_test), label_order)
    holdout_metrics["test_rows"] = int(len(x_test))
    probabilities = best.predict_proba(x_valid)
    predictions = best.predict(x_valid)
    confidence = probabilities.max(axis=1)
    correct_confidence = confidence[predictions == y_valid.to_numpy()]
    confidence_threshold = float(
        np.clip(
            np.percentile(correct_confidence, 20) if len(correct_confidence) else 0.45, 0.35, 0.65
        )
    )

    neighbor_take = min(5_000, len(x_train))
    neighbor_positions = np.linspace(0, len(x_train) - 1, neighbor_take, dtype=int)
    neighbor_frame = x_train.iloc[neighbor_positions]
    neighbor_scaler = RobustScaler().fit(neighbor_frame)
    neighbor_matrix = neighbor_scaler.transform(neighbor_frame).astype("float32")
    neighbor_index = NearestNeighbors(n_neighbors=min(6, neighbor_take), metric="euclidean")
    neighbor_index.fit(neighbor_matrix)
    valid_sample = x_valid.iloc[: min(5_000, len(x_valid))]
    valid_scaled = neighbor_scaler.transform(valid_sample)
    valid_distances, _ = neighbor_index.kneighbors(valid_scaled, n_neighbors=1)
    novelty_threshold = float(np.percentile(valid_distances[:, 0], 95))

    metadata_rows = source_rows.loc[x_train.index].iloc[neighbor_positions]
    neighbor_metadata = [
        {
            "source_id": f"ref-{position + 1:05d}",
            "fault_family": str(row["canonical_fault"]),
            "rpm": float(row["rpm"]),
            "created_at": row["created_at"].isoformat(),
        }
        for position, (_, row) in enumerate(metadata_rows.iterrows())
    ]

    random_x_train, random_x_valid, random_y_train, random_y_valid = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=labels,
    )
    random_estimator = clone(_candidates()[best_name])
    random_x_train, random_y_train, _ = _limit_training_rows(
        random_x_train,
        random_y_train,
        pd.Series(np.arange(len(random_x_train)), index=random_x_train.index),
    )
    random_estimator.fit(random_x_train, random_y_train)
    random_metrics = _metrics(random_y_valid, random_estimator.predict(random_x_valid), label_order)

    version = f"fiesc-2026-{best_name}-v2"
    bundle = ModelBundle(
        estimator=best,
        feature_names=list(MODEL_FEATURES),
        class_labels=label_order,
        confidence_threshold=confidence_threshold,
        novelty_distance_threshold=max(novelty_threshold, 1e-6),
        neighbor_scaler=neighbor_scaler,
        neighbor_index=neighbor_index,
        neighbor_metadata=neighbor_metadata,
        occurrence_counts={str(k): int(v) for k, v in full_occurrence_counts.items()},
        version=version,
    )
    metrics = {
        "selected_model": best_name,
        "model_version": version,
        "group_split": candidate_results,
        "holdout_test": holdout_metrics,
        "random_split_diagnostic": random_metrics,
        "confidence_threshold": confidence_threshold,
        "novelty_distance_threshold": novelty_threshold,
        "train_sessions": int(train_groups.nunique()),
        "validation_sessions": int(groups.iloc[valid_idx].nunique()),
        "test_sessions": int(groups.iloc[test_idx].nunique()),
        "feature_count": len(MODEL_FEATURES),
    }
    return bundle, metrics


def save_model_bundle(
    bundle: ModelBundle,
    metrics: dict[str, Any],
    model_path: Path,
    metadata_path: Path,
    metrics_path: Path,
    audit: dict[str, Any],
) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path, compress=3)
    metadata = {
        "version": bundle.version,
        "model_sha256": _sha256(model_path),
        "library_versions": {
            "python": sys.version.split()[0],
            "numpy": package_version("numpy"),
            "pandas": package_version("pandas"),
            "scikit-learn": package_version("scikit-learn"),
            "joblib": package_version("joblib"),
        },
        "feature_names": bundle.feature_names,
        "class_labels": bundle.class_labels,
        "confidence_threshold": bundle.confidence_threshold,
        "novelty_distance_threshold": bundle.novelty_distance_threshold,
        "occurrence_counts": bundle.occurrence_counts,
        "source_audit": audit,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")


def load_model_bundle(path: Path) -> ModelBundle:
    metadata_path = path.with_name("model_metadata.json")
    if not metadata_path.exists():
        raise FileNotFoundError("Metadados de integridade do modelo ausentes")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    expected_hash = str(metadata.get("model_sha256", "")).lower()
    actual_hash = _sha256(path)
    if not expected_hash or not secrets.compare_digest(expected_hash, actual_hash):
        raise ValueError("Hash SHA-256 do modelo nao confere; carga bloqueada")
    bundle = joblib.load(path)
    if not isinstance(bundle, ModelBundle):
        raise TypeError("Artefato de modelo invalido")
    return bundle
