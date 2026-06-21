#!/usr/bin/env python3
"""Baseline modeling helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any

from dataset_models import Dataset, DataScientistError
from profiling import infer_type, to_decimal


def resolve_feature_columns(dataset: Dataset, target_column: str, feature_columns: list[str] | None) -> list[str]:
    if target_column not in dataset.columns:
        raise DataScientistError(f"target column not found: {target_column}")
    candidates = feature_columns or [column for column in dataset.columns if column != target_column]
    missing = [column for column in candidates if column not in dataset.columns]
    if missing:
        raise DataScientistError(f"feature columns not found: {', '.join(missing)}")
    return [column for column in candidates if column != target_column]


def infer_target_type(values: list[str]) -> str:
    unique = set(values)
    if len(unique) <= 2:
        return "classification"
    if infer_type(values) == "number":
        return "regression"
    return "classification"


def is_numeric_column(dataset: Dataset, column: str) -> bool:
    values = [row.get(column, "") for row in dataset.rows if row.get(column, "") != ""]
    return infer_type(values) == "number"


def numeric_values(rows: list[dict[str, str]], column: str) -> list[float]:
    return [
        float(value)
        for value in (to_decimal(row.get(column, "")) for row in rows)
        if value is not None
    ]


def train_numeric_threshold_model(
    rows: list[dict[str, str]],
    target_column: str,
    feature_columns: list[str],
) -> dict[str, Any]:
    labels = [row.get(target_column, "") for row in rows if row.get(target_column, "") != ""]
    if len(set(labels)) != 2:
        raise DataScientistError("baseline classification requires exactly two target classes")
    negative_label, positive_label = sorted(set(labels))
    best_model: dict[str, Any] | None = None
    for feature in feature_columns:
        values = numeric_values(rows, feature)
        if not values:
            continue
        for threshold in sorted(set(values)):
            model = {
                "type": "numeric_threshold",
                "feature": feature,
                "threshold": threshold,
                "rule": f"{feature} >= {threshold} => {positive_label}",
                "positive_label": positive_label,
                "negative_label": negative_label,
            }
            predictions = [predict_with_model(model, row) for row in rows]
            metrics = classification_metrics([row.get(target_column, "") for row in rows], predictions, positive_label)
            score = metrics["accuracy"]
            if best_model is None or score > best_model["_score"]:
                best_model = {**model, "_score": score}
    if best_model is None:
        majority = Counter(labels).most_common(1)[0][0]
        negative = next((label for label in sorted(set(labels)) if label != majority), majority)
        best_model = {
            "type": "majority_class",
            "feature": None,
            "threshold": None,
            "rule": f"always predict {majority}",
            "positive_label": majority,
            "negative_label": negative,
            "_score": labels.count(majority) / len(labels),
        }
    best_model.pop("_score", None)
    return best_model


def split_modeling_rows(
    rows: list[dict[str, str]],
    target_column: str,
    test_size: float = 0.2,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    valid_rows = [row for row in rows if row.get(target_column, "") != ""]
    warnings = []
    if len(valid_rows) < 5:
        warnings.append("dataset too small for holdout; metrics are in-sample")
        return valid_rows, valid_rows, warnings
    test_count = max(1, round(len(valid_rows) * test_size))
    if test_count >= len(valid_rows):
        test_count = 1
    train_rows = valid_rows[:-test_count]
    test_rows = valid_rows[-test_count:]
    if len({row.get(target_column, "") for row in train_rows}) != 2:
        warnings.append("training split does not contain exactly two target classes; metrics are in-sample")
        return valid_rows, valid_rows, warnings
    if not test_rows:
        warnings.append("empty holdout split; metrics are in-sample")
        return valid_rows, valid_rows, warnings
    return train_rows, test_rows, warnings


def class_balance(rows: list[dict[str, str]], target_column: str) -> dict[str, Any]:
    labels = [row.get(target_column, "") for row in rows if row.get(target_column, "") != ""]
    counts = Counter(labels)
    total = sum(counts.values())
    ratios = {
        label: round(count / total, 6)
        for label, count in sorted(counts.items())
    } if total else {}
    imbalance_ratio = None
    if counts:
        majority = max(counts.values())
        minority = min(counts.values())
        imbalance_ratio = round(minority / majority, 6) if majority else None
    return {
        "total": dict(sorted(counts.items())),
        "ratios": ratios,
        "imbalance_ratio": imbalance_ratio,
    }


def modeling_validity_warnings(
    rows: list[dict[str, str]],
    target_column: str,
    split_warnings: list[str],
) -> list[dict[str, Any]]:
    warnings = [
        {
            "code": "split_fallback",
            "severity": "medium",
            "message": message,
        }
        for message in split_warnings
    ]
    balance = class_balance(rows, target_column)
    imbalance_ratio = balance["imbalance_ratio"]
    if imbalance_ratio is not None and imbalance_ratio < 0.5:
        warnings.append(
            {
                "code": "imbalanced_classes",
                "severity": "medium",
                "message": "Target classes are imbalanced; accuracy can overstate model quality.",
            }
        )
    if len([row for row in rows if row.get(target_column, "") != ""]) < 30:
        warnings.append(
            {
                "code": "small_modeling_sample",
                "severity": "medium",
                "message": "Fewer than 30 labeled rows; baseline metrics can be unstable.",
            }
        )
    return warnings


def predict_with_model(model: dict[str, Any], row: dict[str, str]) -> str:
    if model["type"] == "majority_class":
        return model["positive_label"]
    value = to_decimal(row.get(model["feature"], ""))
    if value is None:
        return model["negative_label"]
    return model["positive_label"] if float(value) >= float(model["threshold"]) else model["negative_label"]


def classification_metrics(actuals: list[str], predictions: list[str], positive_label: str) -> dict[str, Any]:
    pairs = [(actual, predicted) for actual, predicted in zip(actuals, predictions) if actual != ""]
    if not pairs:
        raise DataScientistError("no valid target values for evaluation")
    tp = sum(1 for actual, predicted in pairs if actual == positive_label and predicted == positive_label)
    tn = sum(1 for actual, predicted in pairs if actual != positive_label and predicted != positive_label)
    fp = sum(1 for actual, predicted in pairs if actual != positive_label and predicted == positive_label)
    fn = sum(1 for actual, predicted in pairs if actual == positive_label and predicted != positive_label)
    accuracy = (tp + tn) / len(pairs)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    negative_predictive_value = tn / (tn + fn) if tn + fn else 0.0
    balanced_accuracy = (recall + specificity) / 2
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "accuracy": round(accuracy, 6),
        "balanced_accuracy": round(balanced_accuracy, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "specificity": round(specificity, 6),
        "negative_predictive_value": round(negative_predictive_value, 6),
        "f1": round(f1, 6),
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }


def detect_leakage_candidates(dataset: Dataset, target_column: str) -> list[dict[str, Any]]:
    if target_column not in dataset.columns:
        raise DataScientistError(f"target column not found: {target_column}")
    target_values = [row.get(target_column, "") for row in dataset.rows]
    suspicious_terms = ("post", "after", "approved", "status", "resultado", "result")
    candidates = []
    for column in dataset.columns:
        if column == target_column:
            continue
        values = [row.get(column, "") for row in dataset.rows]
        if values == target_values:
            candidates.append({"column": column, "reason": "exact_target_copy", "severity": "high"})
            continue
        lowered = column.casefold()
        if any(term in lowered for term in suspicious_terms):
            candidates.append({"column": column, "reason": "post_event_or_result_name", "severity": "medium"})
    return candidates
