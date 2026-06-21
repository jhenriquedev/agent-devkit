#!/usr/bin/env python3
"""Statistical helper functions for baseline analysis."""

from __future__ import annotations

import math
import statistics
from typing import Any

from dataset_models import Dataset, DataScientistError
from profiling import to_decimal


def summarize_metric(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "sum": 0.0, "mean": None, "min": None, "max": None}
    return {
        "count": len(values),
        "sum": round(sum(values), 6),
        "mean": round(statistics.fmean(values), 6),
        "min": min(values),
        "max": max(values),
    }


def grouped_metric_values(
    dataset: Dataset,
    group_column: str,
    group_a: str,
    group_b: str,
    metric_column: str,
) -> tuple[list[float], list[float]]:
    for column in (group_column, metric_column):
        if column not in dataset.columns:
            raise DataScientistError(f"column not found: {column}")
    left_values = []
    right_values = []
    for row in dataset.rows:
        metric = to_decimal(row.get(metric_column, ""))
        if metric is None:
            continue
        group_value = row.get(group_column, "")
        if group_value == group_a:
            left_values.append(float(metric))
        elif group_value == group_b:
            right_values.append(float(metric))
    if len(left_values) < 2 or len(right_values) < 2:
        raise DataScientistError("group comparison requires at least two numeric values per group")
    return left_values, right_values


def metric_data_quality(dataset: Dataset, metric_column: str) -> dict[str, int]:
    if metric_column not in dataset.columns:
        raise DataScientistError(f"metric column not found: {metric_column}")
    missing_metric_rows = 0
    non_numeric_metric_rows = 0
    numeric_rows = 0
    for row in dataset.rows:
        raw = row.get(metric_column, "")
        if raw == "":
            missing_metric_rows += 1
            continue
        if to_decimal(raw) is None:
            non_numeric_metric_rows += 1
            continue
        numeric_rows += 1
    return {
        "total_rows": len(dataset.rows),
        "numeric_rows": numeric_rows,
        "missing_metric_rows": missing_metric_rows,
        "non_numeric_metric_rows": non_numeric_metric_rows,
    }


def statistical_assumptions(method: str) -> list[str]:
    if method == "mean_difference_normal_approx":
        return [
            "groups are independent",
            "metric is numeric and comparable across groups",
            "normal approximation is acceptable for the observed sample sizes",
        ]
    if method == "mean_confidence_interval_normal_approx":
        return [
            "sample is representative of the population being described",
            "metric is numeric",
            "normal approximation is acceptable for the observed sample size",
        ]
    return ["baseline statistical approximation"]


def hypothesis_validity_warnings(
    left_values: list[float],
    right_values: list[float],
    data_quality: dict[str, int],
) -> list[dict[str, Any]]:
    warnings = []
    if len(left_values) < 30 or len(right_values) < 30:
        warnings.append(
            {
                "code": "small_group_sample",
                "severity": "medium",
                "message": "At least one group has fewer than 30 numeric observations; normal approximation can be unstable.",
            }
        )
    if data_quality["missing_metric_rows"] or data_quality["non_numeric_metric_rows"]:
        warnings.append(
            {
                "code": "ignored_metric_rows",
                "severity": "medium",
                "message": "Rows with missing or non-numeric metric values were ignored.",
            }
        )
    if statistics.pstdev(left_values) == 0 or statistics.pstdev(right_values) == 0:
        warnings.append(
            {
                "code": "zero_variance_group",
                "severity": "high",
                "message": "At least one group has zero variance; p-value interpretation is limited.",
            }
        )
    return warnings


def confidence_interval_validity_warnings(values: list[float], data_quality: dict[str, int]) -> list[dict[str, Any]]:
    warnings = []
    if len(values) < 30:
        warnings.append(
            {
                "code": "small_sample",
                "severity": "medium",
                "message": "Fewer than 30 numeric values; normal confidence interval can be unstable.",
            }
        )
    if data_quality["missing_metric_rows"] or data_quality["non_numeric_metric_rows"]:
        warnings.append(
            {
                "code": "ignored_metric_rows",
                "severity": "medium",
                "message": "Rows with missing or non-numeric metric values were ignored.",
            }
        )
    return warnings


def mean_difference_standard_error(left_values: list[float], right_values: list[float]) -> float:
    left_variance = statistics.variance(left_values)
    right_variance = statistics.variance(right_values)
    return math.sqrt((left_variance / len(left_values)) + (right_variance / len(right_values)))


def two_tailed_normal_p_value(zscore: float) -> float:
    return max(0.0, min(1.0, 2 * (1 - normal_cdf(abs(zscore)))))


def normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def z_for_confidence(confidence: float) -> float:
    lookup = {
        0.8: 1.281552,
        0.9: 1.644854,
        0.95: 1.959964,
        0.98: 2.326348,
        0.99: 2.575829,
    }
    rounded = round(confidence, 2)
    if rounded in lookup:
        return lookup[rounded]
    raise DataScientistError(f"unsupported confidence level: {confidence}")


def z_for_two_tailed_alpha(alpha: float) -> float:
    lookup = {
        0.1: 1.644854,
        0.05: 1.959964,
        0.01: 2.575829,
    }
    rounded = round(alpha, 2)
    if rounded in lookup:
        return lookup[rounded]
    raise DataScientistError(f"unsupported alpha: {alpha}")


def z_for_power(power: float) -> float:
    lookup = {
        0.8: 0.841621,
        0.85: 1.036433,
        0.9: 1.281552,
        0.95: 1.644854,
    }
    rounded = round(power, 2)
    if rounded in lookup:
        return lookup[rounded]
    raise DataScientistError(f"unsupported power: {power}")


def cohens_d(left_values: list[float], right_values: list[float]) -> float:
    left_stdev = statistics.stdev(left_values)
    right_stdev = statistics.stdev(right_values)
    pooled = math.sqrt(
        (((len(left_values) - 1) * (left_stdev**2)) + ((len(right_values) - 1) * (right_stdev**2)))
        / (len(left_values) + len(right_values) - 2)
    )
    if pooled == 0:
        return 0.0
    return (statistics.fmean(right_values) - statistics.fmean(left_values)) / pooled


def calculate_cohens_d(left_values: list[float], right_values: list[float]) -> float:
    return cohens_d(left_values, right_values)


def effect_magnitude(effect_size: float | None) -> str | None:
    if effect_size is None:
        return None
    absolute = abs(effect_size)
    if absolute >= 0.8:
        return "large"
    if absolute >= 0.5:
        return "medium"
    if absolute >= 0.2:
        return "small"
    return "negligible"


def explain_significance(p_value: float | None, alpha: float, effect_size: float | None) -> dict[str, Any]:
    significant = bool(p_value is not None and p_value < alpha)
    effect = effect_magnitude(effect_size)
    if p_value is None:
        executive = "Resultado inconclusivo porque o p-valor nao foi calculado."
    elif significant:
        executive = f"Resultado estatisticamente significativo para alpha={alpha}."
    else:
        executive = f"Resultado nao significativo para alpha={alpha}."
    return {
        "p_value": p_value,
        "alpha": alpha,
        "significant": significant,
        "effect_size": effect_size,
        "effect_magnitude": effect,
        "executive_summary": executive,
        "technical_notes": [
            "p-valor estima compatibilidade dos dados com a hipotese nula.",
            "Significancia estatistica nao mede impacto pratico nem causalidade.",
        ],
    }
