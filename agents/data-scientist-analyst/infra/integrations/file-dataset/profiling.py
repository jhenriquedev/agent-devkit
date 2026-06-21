#!/usr/bin/env python3
"""Profiling, typing, quality and exploratory helpers."""

from __future__ import annotations

import statistics
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from dataset_models import Dataset, DataScientistError
from privacy import mask_value, normalize_name


def profile_column(column: str, values: list[str]) -> dict[str, Any]:
    non_empty = [value for value in values if value != ""]
    inferred_type = infer_type(non_empty)
    top_values = Counter(non_empty).most_common(5)
    profile: dict[str, Any] = {
        "inferred_type": inferred_type,
        "missing_count": len(values) - len(non_empty),
        "unique_count": len(set(non_empty)),
        "sample_values": [mask_value(column, value) for value in non_empty[:5]],
        "top_values": [
            {"value": mask_value(column, value), "count": count}
            for value, count in top_values
        ],
    }
    if inferred_type == "number":
        numbers = [float(value) for value in (to_decimal(item) for item in non_empty) if value is not None]
        if numbers:
            profile["numeric"] = {
                "min": min(numbers),
                "max": max(numbers),
                "mean": round(statistics.fmean(numbers), 6),
                "median": round(statistics.median(numbers), 6),
            }
    return profile


def resolve_numeric_columns(dataset: Dataset, columns: list[str] | None) -> list[str]:
    candidates = columns or dataset.columns
    selected = []
    missing = [column for column in candidates if column not in dataset.columns]
    if missing:
        raise DataScientistError(f"columns not found: {', '.join(missing)}")
    for column in candidates:
        values = [row.get(column, "") for row in dataset.rows if row.get(column, "") != ""]
        if infer_type(values) == "number":
            selected.append(column)
    return selected


def numeric_values_with_rows(rows: list[dict[str, str]], column: str) -> list[dict[str, Any]]:
    values = []
    for index, row in enumerate(rows, start=1):
        parsed = to_decimal(row.get(column, ""))
        if parsed is not None:
            values.append({"row_number": index, "value": float(parsed)})
    return values


def detect_column_outliers(values: list[dict[str, Any]], method: str, threshold: float) -> dict[str, Any]:
    numbers = [item["value"] for item in values]
    if len(numbers) < 4:
        return {"outlier_count": 0, "outliers": [], "bounds": None}
    outliers = []
    bounds = {}
    normalized = method.lower()
    if normalized in {"iqr", "both"}:
        q1 = percentile(numbers, 25)
        q3 = percentile(numbers, 75)
        iqr = q3 - q1
        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)
        bounds["iqr"] = {"lower": round(lower, 6), "upper": round(upper, 6)}
        for item in values:
            if item["value"] < lower or item["value"] > upper:
                outliers.append({**item, "method": "iqr"})
    if normalized in {"zscore", "both"}:
        mean = statistics.fmean(numbers)
        stdev = statistics.pstdev(numbers)
        bounds["zscore"] = {"mean": round(mean, 6), "stdev": round(stdev, 6), "threshold": threshold}
        if stdev:
            for item in values:
                zscore = (item["value"] - mean) / stdev
                if abs(zscore) > threshold:
                    outliers.append({**item, "method": "zscore", "zscore": round(zscore, 6)})
    deduped = {}
    for item in outliers:
        deduped[item["row_number"]] = item
    return {
        "outlier_count": len(deduped),
        "outliers": sorted(deduped.values(), key=lambda item: item["row_number"])[:50],
        "bounds": bounds,
    }


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * (percent / 100)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def paired_numeric_values(rows: list[dict[str, str]], left: str, right: str) -> list[tuple[float, float]]:
    pairs = []
    for row in rows:
        left_value = to_decimal(row.get(left, ""))
        right_value = to_decimal(row.get(right, ""))
        if left_value is not None and right_value is not None:
            pairs.append((float(left_value), float(right_value)))
    return pairs


def pearson_correlation(left_values: list[float], right_values: list[float]) -> float | None:
    if len(left_values) < 2 or len(right_values) < 2 or len(left_values) != len(right_values):
        return None
    left_mean = statistics.fmean(left_values)
    right_mean = statistics.fmean(right_values)
    numerator = sum((left - left_mean) * (right - right_mean) for left, right in zip(left_values, right_values))
    left_denominator = sum((left - left_mean) ** 2 for left in left_values)
    right_denominator = sum((right - right_mean) ** 2 for right in right_values)
    denominator = (left_denominator * right_denominator) ** 0.5
    if denominator == 0:
        return None
    return numerator / denominator


def correlation_strength(value: float) -> str:
    absolute = abs(value)
    if absolute >= 0.8:
        return "strong"
    if absolute >= 0.5:
        return "moderate"
    if absolute >= 0.3:
        return "weak"
    return "very_weak"


def build_hypotheses(
    profile: dict[str, Any],
    outliers: dict[str, Any],
    correlations: dict[str, Any],
    segments: dict[str, Any] | None,
    target_column: str | None = None,
) -> list[dict[str, Any]]:
    hypotheses = []
    if profile["quality"]["quality_score"] < 80:
        hypotheses.append(
            {
                "priority": "high",
                "hypothesis": "Problemas de qualidade podem afetar conclusoes analiticas.",
                "evidence": profile["quality"],
            }
        )
    for column, details in outliers.get("columns", {}).items():
        if details["outlier_count"]:
            hypotheses.append(
                {
                    "priority": "medium",
                    "hypothesis": f"{column} contem valores extremos que podem distorcer medias.",
                    "evidence": {"outlier_count": details["outlier_count"]},
                }
            )
    if correlations.get("top_correlations"):
        top = correlations["top_correlations"][0]
        hypotheses.append(
            {
                "priority": "medium",
                "hypothesis": f"{top['left']} e {top['right']} apresentam correlacao {top['strength']}.",
                "evidence": top,
            }
        )
    if segments and segments.get("segments"):
        largest = max(segments["segments"], key=lambda item: item["row_count"])
        hypotheses.append(
            {
                "priority": "low",
                "hypothesis": f"Segmento {largest['segment']} concentra a maior quantidade de linhas.",
                "evidence": largest,
            }
        )
    return hypotheses[:10]


def infer_type(values: list[str]) -> str:
    if not values:
        return "unknown"
    numeric_count = sum(1 for value in values if to_decimal(value) is not None)
    date_count = sum(1 for value in values if looks_like_date(value))
    boolean_values = {value.strip().lower() for value in values}
    if numeric_count / len(values) >= 0.8:
        return "number"
    if date_count / len(values) >= 0.8:
        return "date"
    if boolean_values <= {"true", "false", "0", "1", "yes", "no", "sim", "nao", "não"}:
        return "boolean"
    return "string"


def looks_like_date(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            datetime.strptime(stripped[:19], fmt)
            return True
        except ValueError:
            continue
    return False


def to_decimal(value: str) -> Decimal | None:
    normalized = value.strip().replace("R$", "").replace(" ", "")
    if normalized.count(",") == 1 and normalized.count(".") > 1:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif normalized.count(",") == 1 and normalized.count(".") == 0:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        return None


def infer_probable_keys(dataset: Dataset, column_profiles: dict[str, dict[str, Any]]) -> list[str]:
    row_count = len(dataset.rows)
    keys = []
    for column, profile in column_profiles.items():
        lowered = normalize_name(column)
        if row_count and profile["unique_count"] == row_count and profile["missing_count"] == 0:
            keys.append(column)
        elif lowered in {"id", "codigo", "code", "cpf", "cnpj"} and profile["missing_count"] == 0:
            keys.append(column)
    return keys[:10]


def count_duplicate_rows(rows: list[dict[str, str]], columns: list[str]) -> int:
    seen: set[tuple[str, ...]] = set()
    duplicates = 0
    for row in rows:
        signature = tuple(row.get(column, "") for column in columns)
        if signature in seen:
            duplicates += 1
        else:
            seen.add(signature)
    return duplicates


def count_empty_rows(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if all(value == "" for value in row.values()))


def quality_score(row_count: int, column_profiles: dict[str, dict[str, Any]], duplicate_row_count: int) -> int:
    if row_count == 0:
        return 0
    total_cells = row_count * max(len(column_profiles), 1)
    missing = sum(profile["missing_count"] for profile in column_profiles.values())
    duplicate_penalty = duplicate_row_count / row_count
    missing_penalty = missing / total_cells if total_cells else 0
    return max(0, min(100, round(100 - (missing_penalty * 50) - (duplicate_penalty * 30))))
