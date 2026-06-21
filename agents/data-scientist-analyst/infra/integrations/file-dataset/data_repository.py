#!/usr/bin/env python3
"""Local dataset repository for the Data Scientist Analyst agent."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from artifacts import write_artifact
from dataset_controls import DatasetControlError, apply_row_controls, positive_int_or_none
from dataset_io import hash_directory, hash_file, merge_columns, read_csv, read_json, read_jsonl, read_xlsx
from dataset_models import Dataset, DataScientistError
from modeling_tools import (
    classification_metrics,
    class_balance,
    detect_leakage_candidates,
    infer_target_type,
    is_numeric_column,
    modeling_validity_warnings,
    numeric_values,
    predict_with_model,
    resolve_feature_columns,
    split_modeling_rows,
    train_numeric_threshold_model,
)
from privacy import detect_sensitive, mask_row, mask_value
from profiling import (
    build_hypotheses,
    correlation_strength,
    count_duplicate_rows,
    count_empty_rows,
    detect_column_outliers,
    infer_probable_keys,
    paired_numeric_values,
    pearson_correlation,
    profile_column,
    quality_score,
    resolve_numeric_columns,
    numeric_values_with_rows,
    to_decimal,
)
from reconciliation_tools import compare_rows, index_rows, key_to_label, mask_row as reconciliation_mask_row
from reporting import render_data_report, render_reconciliation_report
from statistics_tools import (
    confidence_interval_validity_warnings,
    cohens_d,
    effect_magnitude,
    explain_significance,
    grouped_metric_values,
    hypothesis_validity_warnings,
    mean_difference_standard_error,
    metric_data_quality,
    statistical_assumptions,
    summarize_metric,
    two_tailed_normal_p_value,
    z_for_confidence,
    z_for_power,
    z_for_two_tailed_alpha,
)
from time_series_tools import (
    advance_period,
    aggregate_time_series,
    anomaly_validity_warnings,
    format_period,
    parse_date_value,
    parse_period_label,
    summarize_date_range,
    summarize_trend,
    time_series_data_quality,
)


class DataRepository:
    """Read-only local tabular analysis repository."""

    def __init__(
        self,
        max_rows: int | None = None,
        sample_rows: int | None = None,
        max_file_mb: float | None = None,
    ) -> None:
        try:
            self.max_rows = positive_int_or_none(max_rows, "max_rows")
            self.sample_rows = positive_int_or_none(sample_rows, "sample_rows")
        except DatasetControlError as exc:
            raise DataScientistError(str(exc)) from exc
        self.max_file_mb = max_file_mb

    def ingest_dataset(self, source: str) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        return {
            "dataset": self.dataset_summary(dataset),
            "columns": dataset.columns,
            "sample_rows": [mask_row(row) for row in dataset.rows[:5]],
        }

    def inspect_dataset_schema(self, source: str) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        profile = self.profile_dataset(source)
        return {
            "dataset": profile["dataset"],
            "schema": profile["schema"],
            "columns": {
                column: {
                    "inferred_type": details["inferred_type"],
                    "missing_count": details["missing_count"],
                    "unique_count": details["unique_count"],
                    "sample_values": details["sample_values"],
                }
                for column, details in profile["columns"].items()
            },
            "sensitive_data": profile["sensitive_data"],
        }

    def profile_dataset(self, source: str) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        column_profiles = {
            column: profile_column(column, [row.get(column, "") for row in dataset.rows])
            for column in dataset.columns
        }
        duplicate_row_count = count_duplicate_rows(dataset.rows, dataset.columns)
        sensitive = detect_sensitive(dataset)
        probable_keys = infer_probable_keys(dataset, column_profiles)
        return {
            "dataset": self.dataset_summary(dataset),
            "schema": {
                "columns": dataset.columns,
                "probable_keys": probable_keys,
                "types": {
                    column: details["inferred_type"]
                    for column, details in column_profiles.items()
                },
            },
            "quality": {
                "duplicate_row_count": duplicate_row_count,
                "empty_row_count": count_empty_rows(dataset.rows),
                "columns_with_missing_values": [
                    column
                    for column, details in column_profiles.items()
                    if details["missing_count"] > 0
                ],
                "quality_score": quality_score(
                    row_count=len(dataset.rows),
                    column_profiles=column_profiles,
                    duplicate_row_count=duplicate_row_count,
                ),
            },
            "columns": column_profiles,
            "sensitive_data": sensitive,
        }

    def detect_sensitive_data(self, source: str) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        return {
            "dataset": self.dataset_summary(dataset),
            "sensitive_data": detect_sensitive(dataset),
        }

    def run_exploratory_analysis(
        self,
        source: str,
        target_column: str | None = None,
        segment_column: str | None = None,
    ) -> dict[str, Any]:
        profile = self.profile_dataset(source)
        outliers = self.detect_outliers(source=source, columns=None, method="iqr", threshold=3.0)
        correlations = self.analyze_correlation(
            source=source,
            columns=None,
            target_column=target_column,
        )
        segments = (
            self.segment_data(
                source=source,
                segment_column=segment_column,
                metric_column=target_column,
                max_segments=10,
            )
            if segment_column
            else {"summary": {"segment_count": 0}, "segments": []}
        )
        hypotheses = build_hypotheses(profile, outliers, correlations, segments, target_column)
        return {
            "dataset": profile["dataset"],
            "schema": profile["schema"],
            "quality": profile["quality"],
            "numeric_columns": [
                column
                for column, details in profile["columns"].items()
                if details["inferred_type"] == "number"
            ],
            "categorical_columns": [
                column
                for column, details in profile["columns"].items()
                if details["inferred_type"] == "text"
            ],
            "outliers": outliers,
            "correlations": correlations,
            "segments": segments,
            "hypotheses": hypotheses,
            "limitations": [
                "Analise exploratoria nao demonstra causalidade.",
                "Resultados dependem da qualidade e cobertura da fonte informada.",
            ],
        }

    def detect_outliers(
        self,
        source: str,
        columns: list[str] | None = None,
        method: str = "iqr",
        threshold: float = 3.0,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        numeric_columns = resolve_numeric_columns(dataset, columns)
        result = {}
        for column in numeric_columns:
            values = numeric_values_with_rows(dataset.rows, column)
            if len(values) < 4:
                result[column] = {
                    "method": method,
                    "outlier_count": 0,
                    "outlier_ratio": 0.0,
                    "outliers": [],
                    "limits": {},
                }
                continue
            result[column] = detect_column_outliers(values, method, threshold)
        return {
            "dataset": self.dataset_summary(dataset),
            "method": method,
            "threshold": threshold,
            "columns": result,
        }

    def analyze_correlation(
        self,
        source: str,
        columns: list[str] | None = None,
        target_column: str | None = None,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        numeric_columns = resolve_numeric_columns(dataset, columns)
        pairs = []
        for left_index, left in enumerate(numeric_columns):
            for right in numeric_columns[left_index + 1 :]:
                paired = paired_numeric_values(dataset.rows, left, right)
                if len(paired) < 2:
                    continue
                coefficient = pearson_correlation([item[0] for item in paired], [item[1] for item in paired])
                if coefficient is None:
                    continue
                pairs.append(
                    {
                        "left": left,
                        "right": right,
                        "correlation": round(coefficient, 6),
                        "strength": correlation_strength(coefficient),
                        "sample_size": len(paired),
                    }
                )
        pairs.sort(key=lambda item: abs(item["correlation"]), reverse=True)
        target_pairs = []
        if target_column:
            for item in pairs:
                if item["left"] == target_column:
                    target_pairs.append({"column": item["right"], **item})
                elif item["right"] == target_column:
                    target_pairs.append({"column": item["left"], **item})
            target_pairs.sort(key=lambda item: abs(item["correlation"]), reverse=True)
        return {
            "dataset": self.dataset_summary(dataset),
            "numeric_columns": numeric_columns,
            "target_column": target_column,
            "top_correlations": pairs[:20],
            "target_correlations": target_pairs[:20],
            "limitations": [
                "Correlacao mede associacao linear, nao causalidade.",
                "Colunas com baixa variancia ou poucos pares validos podem ser omitidas.",
            ],
        }

    def segment_data(
        self,
        source: str,
        segment_column: str,
        metric_column: str | None = None,
        max_segments: int = 20,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        if segment_column not in dataset.columns:
            raise DataScientistError(f"segment column not found: {segment_column}")
        if metric_column and metric_column not in dataset.columns:
            raise DataScientistError(f"metric column not found: {metric_column}")
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in dataset.rows:
            segment = row.get(segment_column, "") or "(empty)"
            grouped[segment].append(row)
        segments = []
        total = len(dataset.rows)
        for segment, rows in grouped.items():
            item: dict[str, Any] = {
                "segment": mask_value(segment_column, segment),
                "row_count": len(rows),
                "row_ratio": round(len(rows) / total, 6) if total else 0.0,
            }
            if metric_column:
                metric_values = [float(value) for value in (to_decimal(row.get(metric_column, "")) for row in rows) if value is not None]
                item["metric"] = summarize_metric(metric_values)
            segments.append(item)
        segments.sort(key=lambda item: item["row_count"], reverse=True)
        return {
            "dataset": self.dataset_summary(dataset),
            "segment_column": segment_column,
            "metric_column": metric_column,
            "summary": {
                "segment_count": len(segments),
                "returned_segment_count": min(len(segments), max_segments),
                "total_rows": total,
            },
            "segments": segments[:max_segments],
        }

    def analyze_time_series(
        self,
        source: str,
        date_column: str,
        metric_column: str,
        granularity: str = "day",
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        series = aggregate_time_series(dataset, date_column, metric_column, granularity)
        data_quality = time_series_data_quality(dataset, date_column, metric_column)
        warnings = []
        if data_quality["invalid_date_rows"]:
            warnings.append(f"{data_quality['invalid_date_rows']} rows ignored because {date_column} could not be parsed")
        if data_quality["non_numeric_metric_rows"]:
            warnings.append(f"{data_quality['non_numeric_metric_rows']} rows ignored because {metric_column} is not numeric")
        return {
            "dataset": self.dataset_summary(dataset),
            "date_column": date_column,
            "metric_column": metric_column,
            "granularity": granularity,
            "summary": {
                "period_count": len(series),
                "total_sum": round(sum(item["sum"] for item in series), 6),
                "total_rows": sum(item["row_count"] for item in series),
            },
            "trend": summarize_trend(series),
            "data_quality": data_quality,
            "warnings": warnings,
            "series": series,
            "limitations": [
                "Analise temporal baseline; nao ajusta sazonalidade complexa.",
                "Periodos ausentes so aparecem quando existem linhas na fonte.",
            ],
        }

    def compare_periods(
        self,
        source: str,
        date_column: str,
        metric_column: str,
        baseline_start: str,
        baseline_end: str,
        comparison_start: str,
        comparison_end: str,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        baseline = summarize_date_range(
            dataset,
            date_column,
            metric_column,
            parse_date_value(baseline_start),
            parse_date_value(baseline_end),
        )
        comparison = summarize_date_range(
            dataset,
            date_column,
            metric_column,
            parse_date_value(comparison_start),
            parse_date_value(comparison_end),
        )
        absolute = comparison["sum"] - baseline["sum"]
        percent = None if baseline["sum"] == 0 else round((absolute / baseline["sum"]) * 100, 6)
        return {
            "dataset": self.dataset_summary(dataset),
            "date_column": date_column,
            "metric_column": metric_column,
            "baseline": baseline,
            "comparison": comparison,
            "delta": {
                "absolute": round(absolute, 6),
                "percent": percent,
                "direction": "up" if absolute > 0 else "down" if absolute < 0 else "flat",
            },
        }

    def analyze_cohorts(
        self,
        source: str,
        cohort_column: str,
        event_date_column: str,
        metric_column: str | None = None,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        for column in (cohort_column, event_date_column):
            if column not in dataset.columns:
                raise DataScientistError(f"column not found: {column}")
        if metric_column and metric_column not in dataset.columns:
            raise DataScientistError(f"metric column not found: {metric_column}")
        grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
        for row in dataset.rows:
            cohort_date = parse_date_value(row.get(cohort_column, ""))
            event_date = parse_date_value(row.get(event_date_column, ""))
            if not cohort_date or not event_date:
                continue
            age = max(0, (event_date - cohort_date).days)
            grouped[cohort_date.isoformat()][str(age)].append(row)
        cohorts = []
        for cohort, periods in sorted(grouped.items()):
            cohort_periods = {}
            for period, rows in sorted(periods.items(), key=lambda item: int(item[0])):
                item: dict[str, Any] = {"row_count": len(rows)}
                if metric_column:
                    metric_values = [
                        float(value)
                        for value in (to_decimal(row.get(metric_column, "")) for row in rows)
                        if value is not None
                    ]
                    item["metric"] = summarize_metric(metric_values)
                cohort_periods[period] = item
            cohorts.append({"cohort": cohort, "periods": cohort_periods})
        return {
            "dataset": self.dataset_summary(dataset),
            "cohort_column": cohort_column,
            "event_date_column": event_date_column,
            "metric_column": metric_column,
            "summary": {
                "cohort_count": len(cohorts),
                "period_unit": "days_since_cohort",
            },
            "cohorts": cohorts,
        }

    def detect_anomalies(
        self,
        source: str,
        date_column: str,
        metric_column: str,
        granularity: str = "day",
        threshold: float = 2.0,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        series = aggregate_time_series(dataset, date_column, metric_column, granularity)
        data_quality = time_series_data_quality(dataset, date_column, metric_column)
        values = [item["sum"] for item in series]
        mean = statistics.fmean(values) if values else 0.0
        stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
        anomalies = []
        if stdev > 0:
            for item in series:
                zscore = (item["sum"] - mean) / stdev
                if abs(zscore) > threshold:
                    anomalies.append(
                        {
                            "period": item["period"],
                            "value": item["sum"],
                            "zscore": round(zscore, 6),
                            "direction": "spike" if zscore > 0 else "drop",
                        }
                    )
        return {
            "dataset": self.dataset_summary(dataset),
            "date_column": date_column,
            "metric_column": metric_column,
            "granularity": granularity,
            "method": "zscore",
            "threshold": threshold,
            "baseline": {
                "mean": round(mean, 6),
                "stdev": round(stdev, 6),
            },
            "anomalies": anomalies,
            "series": series,
            "data_quality": data_quality,
            "validity_warnings": anomaly_validity_warnings(series, data_quality),
            "assumptions": [
                "historical periods are comparable",
                "z-score over aggregated sums is appropriate for the monitoring goal",
            ],
            "limitations": [
                "Z-score baseline nao modela sazonalidade, feriados ou mudancas estruturais.",
            ],
        }

    def forecast_series(
        self,
        source: str,
        date_column: str,
        metric_column: str,
        granularity: str = "day",
        periods: int = 3,
        window: int = 3,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        series = aggregate_time_series(dataset, date_column, metric_column, granularity)
        if not series:
            raise DataScientistError("time series has no valid periods")
        periods = max(1, periods)
        window = max(1, window)
        historical = [item["sum"] for item in series]
        last_period = parse_period_label(series[-1]["period"], granularity)
        forecast = []
        generated_values: list[float] = []
        for index in range(1, periods + 1):
            basis = (historical + generated_values)[-window:]
            value = round(statistics.fmean(basis), 6)
            generated_values.append(value)
            period_date = advance_period(last_period, granularity, index)
            forecast.append({"period": format_period(period_date, granularity), "forecast": value})
        return {
            "dataset": self.dataset_summary(dataset),
            "date_column": date_column,
            "metric_column": metric_column,
            "granularity": granularity,
            "method": "moving_average",
            "window": window,
            "historical": series,
            "forecast": forecast,
            "limitations": [
                "Forecast baseline por media movel; nao modela sazonalidade ou eventos externos.",
            ],
        }

    def test_hypothesis(
        self,
        source: str,
        test_type: str,
        group_column: str,
        group_a: str,
        group_b: str,
        metric_column: str,
        alpha: float = 0.05,
    ) -> dict[str, Any]:
        if test_type != "mean-difference":
            raise DataScientistError(f"unsupported test type: {test_type}")
        dataset = self.load_dataset(source)
        left_values, right_values = grouped_metric_values(dataset, group_column, group_a, group_b, metric_column)
        data_quality = metric_data_quality(dataset, metric_column)
        left_summary = summarize_metric(left_values)
        right_summary = summarize_metric(right_values)
        standard_error = mean_difference_standard_error(left_values, right_values)
        difference = right_summary["mean"] - left_summary["mean"]
        zscore = None if standard_error == 0 else difference / standard_error
        p_value = None if zscore is None else round(two_tailed_normal_p_value(zscore), 8)
        return {
            "dataset": self.dataset_summary(dataset),
            "test_type": test_type,
            "alpha": alpha,
            "metric_column": metric_column,
            "group_column": group_column,
            "groups": {
                group_a: left_summary,
                group_b: right_summary,
            },
            "difference": round(difference, 6),
            "standard_error": round(standard_error, 6),
            "zscore": None if zscore is None else round(zscore, 6),
            "p_value": p_value,
            "significant": bool(p_value is not None and p_value < alpha),
            "interpretation": explain_significance(p_value, alpha, None)["executive_summary"],
            "data_quality": data_quality,
            "assumptions": statistical_assumptions("mean_difference_normal_approx"),
            "validity_warnings": hypothesis_validity_warnings(left_values, right_values, data_quality),
            "recommended_next_test": "welch_t_test_or_nonparametric_test",
            "limitations": [
                "Teste usa aproximacao normal e nao substitui validacao estatistica completa.",
                "Significancia estatistica nao implica causalidade.",
            ],
        }

    def calculate_confidence_intervals(
        self,
        source: str,
        metric_column: str,
        confidence: float = 0.95,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        if metric_column not in dataset.columns:
            raise DataScientistError(f"metric column not found: {metric_column}")
        values = [
            float(value)
            for value in (to_decimal(row.get(metric_column, "")) for row in dataset.rows)
            if value is not None
        ]
        data_quality = metric_data_quality(dataset, metric_column)
        if len(values) < 2:
            raise DataScientistError("confidence interval requires at least two numeric values")
        mean = statistics.fmean(values)
        stdev = statistics.stdev(values)
        zvalue = z_for_confidence(confidence)
        margin = zvalue * (stdev / math.sqrt(len(values)))
        return {
            "dataset": self.dataset_summary(dataset),
            "metric_column": metric_column,
            "confidence": confidence,
            "sample_size": len(values),
            "mean": round(mean, 6),
            "standard_deviation": round(stdev, 6),
            "standard_error": round(stdev / math.sqrt(len(values)), 6),
            "z_value": zvalue,
            "interval": {
                "lower": round(mean - margin, 6),
                "upper": round(mean + margin, 6),
                "margin": round(margin, 6),
            },
            "data_quality": data_quality,
            "assumptions": statistical_assumptions("mean_confidence_interval_normal_approx"),
            "validity_warnings": confidence_interval_validity_warnings(values, data_quality),
            "recommended_next_test": "bootstrap_confidence_interval_or_t_interval",
            "limitations": [
                "Intervalo usa aproximacao normal e pressupoe amostra representativa.",
            ],
        }

    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        alpha: float = 0.05,
        power: float = 0.8,
    ) -> dict[str, Any]:
        if not 0 < baseline_rate < 1:
            raise DataScientistError("--baseline-rate must be between 0 and 1")
        if not 0 < minimum_detectable_effect < 1:
            raise DataScientistError("--minimum-detectable-effect must be between 0 and 1")
        z_alpha = z_for_two_tailed_alpha(alpha)
        z_power = z_for_power(power)
        variance = baseline_rate * (1 - baseline_rate)
        per_group = math.ceil(2 * ((z_alpha + z_power) ** 2) * variance / (minimum_detectable_effect**2))
        return {
            "method": "two_proportions_normal_approx",
            "baseline_rate": baseline_rate,
            "minimum_detectable_effect": minimum_detectable_effect,
            "alpha": alpha,
            "power": power,
            "z_alpha": z_alpha,
            "z_power": z_power,
            "sample_size_per_group": per_group,
            "total_sample_size": per_group * 2,
            "limitations": [
                "Estimativa baseline para duas proporcoes balanceadas.",
                "Amostras reais podem exigir ajuste por perdas, segmentacao ou desenho experimental.",
            ],
        }

    def measure_effect_size(
        self,
        source: str,
        group_column: str,
        group_a: str,
        group_b: str,
        metric_column: str,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        left_values, right_values = grouped_metric_values(dataset, group_column, group_a, group_b, metric_column)
        effect = cohens_d(left_values, right_values)
        return {
            "dataset": self.dataset_summary(dataset),
            "method": "cohens_d",
            "metric_column": metric_column,
            "group_column": group_column,
            "groups": {
                group_a: summarize_metric(left_values),
                group_b: summarize_metric(right_values),
            },
            "effect_size": round(effect, 6),
            "magnitude": effect_magnitude(effect),
            "limitations": [
                "Cohen's d resume diferenca padronizada de medias; nao mede causalidade.",
            ],
        }

    def explain_statistical_result(
        self,
        p_value: float,
        alpha: float = 0.05,
        effect_size: float | None = None,
    ) -> dict[str, Any]:
        return explain_significance(p_value, alpha, effect_size)

    def prepare_modeling_dataset(
        self,
        source: str,
        target_column: str,
        feature_columns: list[str] | None = None,
        test_size: float = 0.2,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        features = resolve_feature_columns(dataset, target_column, feature_columns)
        target_values = [row.get(target_column, "") for row in dataset.rows if row.get(target_column, "") != ""]
        target_type = infer_target_type(target_values)
        test_rows = min(len(dataset.rows), max(1, round(len(dataset.rows) * test_size))) if dataset.rows else 0
        train_rows = max(0, len(dataset.rows) - test_rows)
        leakage = detect_leakage_candidates(dataset, target_column)
        return {
            "dataset": self.dataset_summary(dataset),
            "target": {
                "column": target_column,
                "type": target_type,
                "unique_values": sorted(set(target_values))[:20],
            },
            "features": {
                "selected": features,
                "numeric": [column for column in features if is_numeric_column(dataset, column)],
                "categorical": [column for column in features if not is_numeric_column(dataset, column)],
            },
            "split": {
                "strategy": "deterministic_tail_holdout",
                "test_size": test_size,
                "train_rows": train_rows,
                "test_rows": test_rows,
            },
            "warnings": leakage[:10],
        }

    def baseline_predictive_model(
        self,
        source: str,
        target_column: str,
        feature_columns: list[str] | None = None,
        test_size: float = 0.2,
    ) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        features = resolve_feature_columns(dataset, target_column, feature_columns)
        train_rows, test_rows, split_warnings = split_modeling_rows(dataset.rows, target_column, test_size)
        model = train_numeric_threshold_model(train_rows, target_column, features)
        train_predictions = [predict_with_model(model, row) for row in train_rows]
        test_predictions = [predict_with_model(model, row) for row in test_rows]
        train_metrics = classification_metrics(
            [row.get(target_column, "") for row in train_rows],
            train_predictions,
            model["positive_label"],
        )
        test_metrics = classification_metrics(
            [row.get(target_column, "") for row in test_rows],
            test_predictions,
            model["positive_label"],
        )
        evaluation_scope = "in_sample_baseline" if train_rows is test_rows else "holdout_baseline"
        total_balance = class_balance(dataset.rows, target_column)
        train_balance = class_balance(train_rows, target_column)
        test_balance = class_balance(test_rows, target_column)
        class_balance_payload = {
            "total": total_balance["total"],
            "total_ratios": total_balance["ratios"],
            "imbalance_ratio": total_balance["imbalance_ratio"],
            "train": train_balance["total"],
            "train_ratios": train_balance["ratios"],
            "test": test_balance["total"],
            "test_ratios": test_balance["ratios"],
        }
        validity_warnings = modeling_validity_warnings(dataset.rows, target_column, split_warnings)
        return {
            "dataset": self.dataset_summary(dataset),
            "target_column": target_column,
            "feature_columns": features,
            "model": model,
            "metrics": test_metrics,
            "train_metrics": train_metrics,
            "test_metrics": test_metrics,
            "evaluation_scope": evaluation_scope,
            "split": {
                "strategy": "deterministic_tail_holdout" if evaluation_scope == "holdout_baseline" else "in_sample_fallback",
                "test_size": test_size,
                "train_rows": len(train_rows),
                "test_rows": len(test_rows),
            },
            "warnings": split_warnings,
            "class_balance": class_balance_payload,
            "validity_warnings": validity_warnings,
            "assumptions": [
                "numeric threshold baseline is appropriate as a simple benchmark",
                "holdout rows are representative of future data when evaluation_scope is holdout_baseline",
            ],
            "limitations": [
                "Modelo baseline simples e explicavel; nao substitui treinamento robusto.",
                "Metricas principais sao calculadas no holdout quando ha dados suficientes.",
            ],
        }

    def evaluate_model(
        self,
        source: str,
        target_column: str,
        feature_columns: list[str] | None = None,
        test_size: float = 0.2,
    ) -> dict[str, Any]:
        payload = self.baseline_predictive_model(source, target_column, feature_columns, test_size)
        model = payload["model"]
        return {
            "dataset": payload["dataset"],
            "target_column": target_column,
            "model": model,
            "metrics": payload["metrics"],
            "train_metrics": payload["train_metrics"],
            "test_metrics": payload["test_metrics"],
            "confusion_matrix": payload["metrics"]["confusion_matrix"],
            "evaluation_scope": payload["evaluation_scope"],
            "split": payload["split"],
            "warnings": payload["warnings"],
            "class_balance": payload["class_balance"],
            "validity_warnings": payload["validity_warnings"],
            "assumptions": payload["assumptions"],
            "limitations": payload["limitations"],
        }

    def explain_model_results(
        self,
        source: str,
        target_column: str,
        feature_columns: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = self.baseline_predictive_model(source, target_column, feature_columns)
        model = payload["model"]
        primary_driver = {
            "feature": model.get("feature"),
            "rule": model.get("rule"),
            "threshold": model.get("threshold"),
        }
        summary = (
            f"O baseline selecionou {primary_driver['feature']} como principal driver "
            f"com a regra {primary_driver['rule']}."
        )
        return {
            "dataset": payload["dataset"],
            "target_column": target_column,
            "primary_driver": primary_driver,
            "metrics": payload["metrics"],
            "executive_summary": summary,
            "limitations": [
                "Driver selecionado representa associacao preditiva na amostra, nao causalidade.",
                "Validar em holdout real antes de usar em decisao operacional.",
            ],
        }

    def detect_data_leakage(self, source: str, target_column: str) -> dict[str, Any]:
        dataset = self.load_dataset(source)
        return {
            "dataset": self.dataset_summary(dataset),
            "target_column": target_column,
            "leakage_candidates": detect_leakage_candidates(dataset, target_column),
        }

    def monitor_model_drift(
        self,
        reference_source: str,
        source: str,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        reference = self.load_dataset(reference_source)
        current = self.load_dataset(source)
        selected = columns or [column for column in reference.columns if column in current.columns]
        drift_rows = []
        for column in selected:
            if column not in reference.columns or column not in current.columns:
                raise DataScientistError(f"column not found in both datasets: {column}")
            if not is_numeric_column(reference, column) or not is_numeric_column(current, column):
                continue
            ref_values = numeric_values(reference.rows, column)
            cur_values = numeric_values(current.rows, column)
            if not ref_values or not cur_values:
                continue
            ref_mean = statistics.fmean(ref_values)
            cur_mean = statistics.fmean(cur_values)
            ref_stdev = statistics.pstdev(ref_values) or 1.0
            drift_score = abs(cur_mean - ref_mean) / ref_stdev
            drift_rows.append(
                {
                    "column": column,
                    "reference_mean": round(ref_mean, 6),
                    "current_mean": round(cur_mean, 6),
                    "mean_delta": round(cur_mean - ref_mean, 6),
                    "drift_score": round(drift_score, 6),
                    "drifted": drift_score >= 2.0,
                }
            )
        return {
            "reference_dataset": self.dataset_summary(reference),
            "current_dataset": self.dataset_summary(current),
            "method": "mean_shift_over_reference_stdev",
            "columns": drift_rows,
            "drifted_columns": [row for row in drift_rows if row["drifted"]],
        }

    def reconcile_spreadsheets(
        self,
        left: str,
        right: str,
        key: str,
        compare_columns: list[str] | None = None,
        numeric_tolerance: Decimal = Decimal("0"),
    ) -> dict[str, Any]:
        left_dataset = self.load_dataset(left)
        right_dataset = self.load_dataset(right)
        keys = [item.strip() for item in key.split(",") if item.strip()]
        if not keys:
            raise DataScientistError("inform at least one --key column")
        missing = [
            f"left.{column}"
            for column in keys
            if column not in left_dataset.columns
        ] + [
            f"right.{column}"
            for column in keys
            if column not in right_dataset.columns
        ]
        if missing:
            raise DataScientistError(f"missing key columns: {', '.join(missing)}")
        if compare_columns is None:
            compare_columns = [
                column
                for column in left_dataset.columns
                if column in right_dataset.columns and column not in keys
            ]
        left_index = index_rows(left_dataset.rows, keys)
        right_index = index_rows(right_dataset.rows, keys)
        matched: list[dict[str, Any]] = []
        mismatched: list[dict[str, Any]] = []
        missing_right: list[dict[str, Any]] = []
        missing_left: list[dict[str, Any]] = []
        duplicate_keys = []
        all_keys = sorted(set(left_index) | set(right_index))

        for composite_key in all_keys:
            left_rows = left_index.get(composite_key, [])
            right_rows = right_index.get(composite_key, [])
            key_label = key_to_label(composite_key)
            if len(left_rows) > 1 or len(right_rows) > 1:
                duplicate_keys.append(
                    {
                        "key": key_label,
                        "left_count": len(left_rows),
                        "right_count": len(right_rows),
                    }
                )
            if not left_rows:
                missing_left.append({"key": key_label, "right": mask_row(right_rows[0])})
                continue
            if not right_rows:
                missing_right.append({"key": key_label, "left": mask_row(left_rows[0])})
                continue
            differences = compare_rows(
                left_rows[0],
                right_rows[0],
                compare_columns,
                numeric_tolerance,
            )
            if differences:
                mismatched.append({"key": key_label, "differences": differences})
            else:
                matched.append({"key": key_label})

        return {
            "sources": {
                "left": self.dataset_summary(left_dataset),
                "right": self.dataset_summary(right_dataset),
            },
            "rules": {
                "key": keys,
                "compare_columns": compare_columns,
                "numeric_tolerance": str(numeric_tolerance),
            },
            "summary": {
                "matched_count": len(matched),
                "mismatched_count": len(mismatched),
                "missing_right_count": len(missing_right),
                "missing_left_count": len(missing_left),
                "duplicate_key_count": len(duplicate_keys),
            },
            "matched": matched,
            "mismatched": mismatched,
            "missing_right": missing_right,
            "missing_left": missing_left,
            "duplicate_keys": duplicate_keys,
        }

    def generate_reconciliation_report(
        self,
        left: str,
        right: str,
        key: str,
        compare_columns: list[str] | None,
        numeric_tolerance: Decimal,
        output: str | None = None,
    ) -> dict[str, Any]:
        payload = self.reconcile_spreadsheets(
            left=left,
            right=right,
            key=key,
            compare_columns=compare_columns,
            numeric_tolerance=numeric_tolerance,
        )
        content = render_reconciliation_report(payload)
        written = write_artifact(content, output)
        payload["report"] = {"format": "markdown", "output": written, "content": content}
        return payload

    def generate_data_report(self, source: str, output: str | None = None) -> dict[str, Any]:
        payload = self.profile_dataset(source)
        content = render_data_report(payload)
        written = write_artifact(content, output)
        return {"profile": payload, "report": {"format": "markdown", "output": written, "content": content}}

    def load_dataset(self, source: str) -> Dataset:
        path = Path(source).expanduser().resolve()
        if not path.exists():
            raise DataScientistError(f"source not found: {source}")
        if path.is_file() and self.max_file_mb is not None:
            max_bytes = self.max_file_mb * 1024 * 1024
            if path.stat().st_size > max_bytes:
                raise DataScientistError(f"source exceeds --max-file-mb: {source}")
        if path.is_dir():
            rows: list[dict[str, str]] = []
            columns: list[str] = []
            warnings: list[str] = []
            original_row_count = 0
            files = [
                item
                for item in sorted(path.iterdir())
                if item.is_file() and item.suffix.lower() in {".csv", ".json", ".jsonl"}
            ]
            if not files:
                raise DataScientistError(f"directory has no supported dataset files: {source}")
            for item in files:
                dataset = self.load_dataset(str(item))
                columns = merge_columns(columns, dataset.columns)
                original_row_count += dataset.original_row_count or len(dataset.rows)
                warnings.extend(dataset.warnings)
                rows.extend(dataset.rows)
            rows, control_warnings, original_row_count = apply_row_controls(
                rows=rows,
                max_rows=self.max_rows,
                sample_rows=self.sample_rows,
                original_row_count=original_row_count,
            )
            warnings.extend(control_warnings)
            return Dataset(
                source=str(path),
                name=path.name,
                format="directory",
                rows=rows,
                columns=columns,
                sha256=hash_directory(files),
                original_row_count=original_row_count,
                warnings=warnings,
            )
        suffix = path.suffix.lower()
        if suffix == ".csv":
            rows, columns = read_csv(path)
        elif suffix == ".json":
            rows, columns = read_json(path)
        elif suffix == ".jsonl":
            rows, columns = read_jsonl(path)
        elif suffix == ".xlsx":
            rows, columns = read_xlsx(path)
        else:
            raise DataScientistError(f"unsupported dataset format: {suffix or path.name}")
        rows, warnings, original_row_count = apply_row_controls(
            rows=rows,
            max_rows=self.max_rows,
            sample_rows=self.sample_rows,
        )
        return Dataset(
            source=str(path),
            name=path.name,
            format=suffix.lstrip("."),
            rows=rows,
            columns=columns,
            sha256=hash_file(path),
            original_row_count=original_row_count,
            warnings=warnings,
        )

    def dataset_summary(self, dataset: Dataset) -> dict[str, Any]:
        return {
            "source": dataset.source,
            "name": dataset.name,
            "format": dataset.format,
            "row_count": len(dataset.rows),
            "original_row_count": dataset.original_row_count or len(dataset.rows),
            "truncated": (dataset.original_row_count or len(dataset.rows)) > len(dataset.rows),
            "column_count": len(dataset.columns),
            "sha256": dataset.sha256,
            "warnings": dataset.warnings,
        }
