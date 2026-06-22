#!/usr/bin/env python3
"""Shared runner helpers for data-scientist-analyst capabilities."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


CAPABILITIES_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = CAPABILITIES_DIR.parent
ROOT = AGENT_DIR.parents[1]
DATASET_DIR = AGENT_DIR / "infra" / "integrations" / "file-dataset"

sys.path.insert(0, str(DATASET_DIR))

from artifacts import write_artifact  # pylint: disable=import-error
from data_repository import DataRepository, DataScientistError  # pylint: disable=import-error
from sql_result import normalize_sql_result, write_tabular_artifact  # pylint: disable=import-error


def run_dataset_capability(capability: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run data-scientist-analyst/{capability}")
    add_common_args(parser)
    args = parser.parse_args()
    try:
        payload = execute(capability, args)
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output and capability not in {"generate-data-report", "generate-reconciliation-report", "run-data-pipeline"}:
            write_artifact(content, args.output)
        print(content, end="")
    except (DataScientistError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source")
    parser.add_argument("--left")
    parser.add_argument("--right")
    parser.add_argument("--key")
    parser.add_argument("--compare-columns")
    parser.add_argument("--columns")
    parser.add_argument("--numeric-tolerance", default="0")
    parser.add_argument("--method", choices=["iqr", "zscore", "both"], default="iqr")
    parser.add_argument("--threshold", type=float, default=3.0)
    parser.add_argument("--target-column")
    parser.add_argument("--segment-column")
    parser.add_argument("--metric-column")
    parser.add_argument("--max-segments", type=int, default=20)
    parser.add_argument("--date-column")
    parser.add_argument("--granularity", choices=["day", "week", "month"], default="day")
    parser.add_argument("--baseline-start")
    parser.add_argument("--baseline-end")
    parser.add_argument("--comparison-start")
    parser.add_argument("--comparison-end")
    parser.add_argument("--cohort-column")
    parser.add_argument("--event-date-column")
    parser.add_argument("--periods", type=int, default=3)
    parser.add_argument("--window", type=int, default=3)
    parser.add_argument("--test-type")
    parser.add_argument("--group-column")
    parser.add_argument("--group-a")
    parser.add_argument("--group-b")
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--baseline-rate", type=float)
    parser.add_argument("--minimum-detectable-effect", type=float)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.8)
    parser.add_argument("--p-value", type=float)
    parser.add_argument("--effect-size", type=float)
    parser.add_argument("--feature-columns")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--model-type", default="auto")
    parser.add_argument("--reference-source")
    parser.add_argument("--output")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--sample-rows", type=int)
    parser.add_argument("--max-file-mb", type=float)
    parser.add_argument("--sheet")
    parser.add_argument("--json-path")
    parser.add_argument("--dataset-output")
    parser.add_argument("--database-agent", choices=["postgres-data-analyzer", "sqlserver-data-analyzer"])
    parser.add_argument("--database-capability", default="profile-table")
    parser.add_argument("--database")
    parser.add_argument("--schema")
    parser.add_argument("--table")
    parser.add_argument("--query")
    parser.add_argument("--limit")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")


def execute(capability: str, args: argparse.Namespace) -> dict[str, Any]:
    repo = DataRepository(
        max_rows=args.max_rows,
        sample_rows=args.sample_rows,
        max_file_mb=args.max_file_mb,
        sheet=args.sheet,
        json_path=args.json_path,
    )
    if capability == "ingest-dataset":
        require(args.source, "--source")
        return repo.ingest_dataset(args.source)
    if capability == "inspect-dataset-schema":
        require(args.source, "--source")
        return repo.inspect_dataset_schema(args.source)
    if capability == "profile-dataset":
        require(args.source, "--source")
        return repo.profile_dataset(args.source)
    if capability == "detect-sensitive-data":
        require(args.source, "--source")
        return repo.detect_sensitive_data(args.source)
    if capability == "run-exploratory-analysis":
        require(args.source, "--source")
        return repo.run_exploratory_analysis(
            source=args.source,
            target_column=args.target_column,
            segment_column=args.segment_column,
        )
    if capability == "run-data-pipeline":
        require(args.source, "--source")
        require(args.output, "--output")
        return repo.run_data_pipeline(
            source=args.source,
            output=args.output,
            target_column=args.target_column,
            segment_column=args.segment_column,
        )
    if capability == "detect-outliers":
        require(args.source, "--source")
        return repo.detect_outliers(
            source=args.source,
            columns=parse_columns(args.columns),
            method=args.method,
            threshold=args.threshold,
        )
    if capability == "analyze-correlation":
        require(args.source, "--source")
        return repo.analyze_correlation(
            source=args.source,
            columns=parse_columns(args.columns),
            target_column=args.target_column,
        )
    if capability == "segment-data":
        require(args.source, "--source")
        require(args.segment_column, "--segment-column")
        return repo.segment_data(
            source=args.source,
            segment_column=args.segment_column,
            metric_column=args.metric_column,
            max_segments=args.max_segments,
        )
    if capability == "analyze-time-series":
        require(args.source, "--source")
        require(args.date_column, "--date-column")
        require(args.metric_column, "--metric-column")
        return repo.analyze_time_series(
            source=args.source,
            date_column=args.date_column,
            metric_column=args.metric_column,
            granularity=args.granularity,
        )
    if capability == "compare-periods":
        require(args.source, "--source")
        require(args.date_column, "--date-column")
        require(args.metric_column, "--metric-column")
        require(args.baseline_start, "--baseline-start")
        require(args.baseline_end, "--baseline-end")
        require(args.comparison_start, "--comparison-start")
        require(args.comparison_end, "--comparison-end")
        return repo.compare_periods(
            source=args.source,
            date_column=args.date_column,
            metric_column=args.metric_column,
            baseline_start=args.baseline_start,
            baseline_end=args.baseline_end,
            comparison_start=args.comparison_start,
            comparison_end=args.comparison_end,
        )
    if capability == "analyze-cohorts":
        require(args.source, "--source")
        require(args.cohort_column, "--cohort-column")
        require(args.event_date_column, "--event-date-column")
        return repo.analyze_cohorts(
            source=args.source,
            cohort_column=args.cohort_column,
            event_date_column=args.event_date_column,
            metric_column=args.metric_column,
        )
    if capability == "detect-anomalies":
        require(args.source, "--source")
        require(args.date_column, "--date-column")
        require(args.metric_column, "--metric-column")
        return repo.detect_anomalies(
            source=args.source,
            date_column=args.date_column,
            metric_column=args.metric_column,
            granularity=args.granularity,
            threshold=args.threshold,
        )
    if capability == "forecast-series":
        require(args.source, "--source")
        require(args.date_column, "--date-column")
        require(args.metric_column, "--metric-column")
        return repo.forecast_series(
            source=args.source,
            date_column=args.date_column,
            metric_column=args.metric_column,
            granularity=args.granularity,
            periods=args.periods,
            window=args.window,
        )
    if capability == "test-hypothesis":
        require(args.source, "--source")
        require(args.test_type, "--test-type")
        require(args.group_column, "--group-column")
        require(args.group_a, "--group-a")
        require(args.group_b, "--group-b")
        require(args.metric_column, "--metric-column")
        return repo.test_hypothesis(
            source=args.source,
            test_type=args.test_type,
            group_column=args.group_column,
            group_a=args.group_a,
            group_b=args.group_b,
            metric_column=args.metric_column,
            alpha=args.alpha,
        )
    if capability == "calculate-confidence-intervals":
        require(args.source, "--source")
        require(args.metric_column, "--metric-column")
        return repo.calculate_confidence_intervals(
            source=args.source,
            metric_column=args.metric_column,
            confidence=args.confidence,
        )
    if capability == "calculate-sample-size":
        if args.baseline_rate is None:
            raise ValueError("missing required argument: --baseline-rate")
        if args.minimum_detectable_effect is None:
            raise ValueError("missing required argument: --minimum-detectable-effect")
        return repo.calculate_sample_size(
            baseline_rate=args.baseline_rate,
            minimum_detectable_effect=args.minimum_detectable_effect,
            alpha=args.alpha,
            power=args.power,
        )
    if capability == "measure-effect-size":
        require(args.source, "--source")
        require(args.group_column, "--group-column")
        require(args.group_a, "--group-a")
        require(args.group_b, "--group-b")
        require(args.metric_column, "--metric-column")
        return repo.measure_effect_size(
            source=args.source,
            group_column=args.group_column,
            group_a=args.group_a,
            group_b=args.group_b,
            metric_column=args.metric_column,
        )
    if capability == "explain-statistical-result":
        if args.p_value is None:
            raise ValueError("missing required argument: --p-value")
        return repo.explain_statistical_result(
            p_value=args.p_value,
            alpha=args.alpha,
            effect_size=args.effect_size,
        )
    if capability == "prepare-modeling-dataset":
        require(args.source, "--source")
        require(args.target_column, "--target-column")
        return repo.prepare_modeling_dataset(
            source=args.source,
            target_column=args.target_column,
            feature_columns=parse_columns(args.feature_columns),
            test_size=args.test_size,
        )
    if capability == "baseline-predictive-model":
        require(args.source, "--source")
        require(args.target_column, "--target-column")
        return repo.baseline_predictive_model(
            source=args.source,
            target_column=args.target_column,
            feature_columns=parse_columns(args.feature_columns),
            test_size=args.test_size,
        )
    if capability == "evaluate-model":
        require(args.source, "--source")
        require(args.target_column, "--target-column")
        return repo.evaluate_model(
            source=args.source,
            target_column=args.target_column,
            feature_columns=parse_columns(args.feature_columns),
            test_size=args.test_size,
        )
    if capability == "explain-model-results":
        require(args.source, "--source")
        require(args.target_column, "--target-column")
        return repo.explain_model_results(
            source=args.source,
            target_column=args.target_column,
            feature_columns=parse_columns(args.feature_columns),
        )
    if capability == "detect-data-leakage":
        require(args.source, "--source")
        require(args.target_column, "--target-column")
        return repo.detect_data_leakage(source=args.source, target_column=args.target_column)
    if capability == "monitor-model-drift":
        require(args.reference_source, "--reference-source")
        require(args.source, "--source")
        return repo.monitor_model_drift(
            reference_source=args.reference_source,
            source=args.source,
            columns=parse_columns(args.columns),
        )
    if capability == "reconcile-spreadsheets":
        require(args.left, "--left")
        require(args.right, "--right")
        require(args.key, "--key")
        return repo.reconcile_spreadsheets(
            left=args.left,
            right=args.right,
            key=args.key,
            compare_columns=parse_columns(args.compare_columns),
            numeric_tolerance=parse_decimal(args.numeric_tolerance),
        )
    if capability == "generate-reconciliation-report":
        require(args.left, "--left")
        require(args.right, "--right")
        require(args.key, "--key")
        return repo.generate_reconciliation_report(
            left=args.left,
            right=args.right,
            key=args.key,
            compare_columns=parse_columns(args.compare_columns),
            numeric_tolerance=parse_decimal(args.numeric_tolerance),
            output=args.output,
        )
    if capability == "generate-data-report":
        require(args.source, "--source")
        return repo.generate_data_report(source=args.source, output=args.output)
    if capability == "analyze-sql-source":
        return analyze_sql_source(args)
    raise ValueError(f"unsupported capability: {capability}")


def analyze_sql_source(args: argparse.Namespace) -> dict[str, Any]:
    require(args.database_agent, "--database-agent")
    command = [
        sys.executable,
        str(ROOT / "ai-devkit"),
        "--json",
        "run",
        args.database_agent,
        args.database_capability,
    ]
    for option, value in (
        ("--database", args.database),
        ("--schema", args.schema),
        ("--table", args.table),
        ("--query", args.query),
        ("--limit", args.limit),
    ):
        if value:
            command.extend([option, value])
    process = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        raise DataScientistError(process.stderr.strip() or f"database agent failed: {process.returncode}")
    payload = json.loads(process.stdout)
    stdout = payload.get("stdout") or "{}"
    try:
        result = json.loads(stdout)
    except json.JSONDecodeError:
        result = {"raw_output": stdout}
    normalized = normalize_sql_result(result)
    artifact = write_tabular_artifact(normalized, args.dataset_output)
    quality_gates = [
        {
            "name": "delegation_success",
            "status": "pass",
            "message": f"{args.database_agent}.{args.database_capability} executado com sucesso.",
        },
        {
            "name": "tabular_result_available",
            "status": "pass" if normalized.get("kind") == "tabular_dataset" else "warning",
            "message": "Resultado tabular normalizado." if normalized.get("kind") == "tabular_dataset" else "Resultado SQL nao tabular; revisar raw_output.",
        },
        {
            "name": "dataset_artifact_written",
            "status": "pass" if artifact else "warning",
            "message": "Artifact tabular gravado." if artifact else "Nenhum --dataset-output informado ou resultado nao tabular.",
        },
    ]
    response = {
        "delegation": {
            "agent": args.database_agent,
            "capability": args.database_capability,
            "status": "success",
        },
        "analysis": normalized,
        "quality_gates": quality_gates,
        "delegated_to": args.database_agent,
        "database_capability": args.database_capability,
        "result": normalized,
    }
    if artifact:
        response["artifact"] = artifact
    return response


def parse_columns(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid --numeric-tolerance: {value}") from exc


def require(value: str | None, name: str) -> None:
    if not value:
        raise ValueError(f"missing required argument: {name}")
