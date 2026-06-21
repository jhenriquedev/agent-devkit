#!/usr/bin/env python3
"""Time-series and date helpers for baseline analysis."""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from dataset_models import Dataset, DataScientistError
from profiling import to_decimal
from statistics_tools import summarize_metric


def aggregate_time_series(
    dataset: Dataset,
    date_column: str,
    metric_column: str,
    granularity: str,
) -> list[dict[str, Any]]:
    for column in (date_column, metric_column):
        if column not in dataset.columns:
            raise DataScientistError(f"column not found: {column}")
    grouped: dict[str, list[float]] = defaultdict(list)
    row_counts: dict[str, int] = defaultdict(int)
    for row in dataset.rows:
        parsed_date = parse_date_value(row.get(date_column, ""))
        metric_value = to_decimal(row.get(metric_column, ""))
        if not parsed_date or metric_value is None:
            continue
        period = format_period(bucket_date(parsed_date, granularity), granularity)
        grouped[period].append(float(metric_value))
        row_counts[period] += 1
    series = []
    for period in sorted(grouped, key=lambda item: parse_period_label(item, granularity)):
        values = grouped[period]
        series.append(
            {
                "period": period,
                "row_count": row_counts[period],
                "sum": round(sum(values), 6),
                "mean": round(statistics.fmean(values), 6),
                "min": min(values),
                "max": max(values),
            }
        )
    return series


def time_series_data_quality(dataset: Dataset, date_column: str, metric_column: str) -> dict[str, int]:
    invalid_date_rows = 0
    non_numeric_metric_rows = 0
    usable_rows = 0
    for row in dataset.rows:
        parsed_date = parse_date_value(row.get(date_column, ""))
        metric_value = to_decimal(row.get(metric_column, ""))
        if not parsed_date:
            invalid_date_rows += 1
            continue
        if metric_value is None:
            non_numeric_metric_rows += 1
            continue
        usable_rows += 1
    return {
        "total_rows": len(dataset.rows),
        "usable_rows": usable_rows,
        "invalid_date_rows": invalid_date_rows,
        "non_numeric_metric_rows": non_numeric_metric_rows,
    }


def anomaly_validity_warnings(series: list[dict[str, Any]], data_quality: dict[str, int]) -> list[dict[str, Any]]:
    warnings = []
    if len(series) < 5:
        warnings.append(
            {
                "code": "short_time_series",
                "severity": "medium",
                "message": "Fewer than 5 periods; z-score anomaly detection can be unstable.",
            }
        )
    if data_quality["invalid_date_rows"] or data_quality["non_numeric_metric_rows"]:
        warnings.append(
            {
                "code": "ignored_time_series_rows",
                "severity": "medium",
                "message": "Rows with invalid dates or non-numeric metric values were ignored.",
            }
        )
    return warnings


def summarize_trend(series: list[dict[str, Any]]) -> dict[str, Any]:
    if len(series) < 2:
        return {"direction": "insufficient_data", "delta": None, "percent": None}
    first = series[0]["sum"]
    last = series[-1]["sum"]
    delta = last - first
    percent = None if first == 0 else round((delta / first) * 100, 6)
    return {
        "direction": "up" if delta > 0 else "down" if delta < 0 else "flat",
        "delta": round(delta, 6),
        "percent": percent,
        "first_period": series[0]["period"],
        "last_period": series[-1]["period"],
    }


def summarize_date_range(
    dataset: Dataset,
    date_column: str,
    metric_column: str,
    start: date | None,
    end: date | None,
) -> dict[str, Any]:
    if not start or not end:
        raise DataScientistError("invalid date range")
    if start > end:
        raise DataScientistError("range start must be before range end")
    values = []
    row_count = 0
    for row in dataset.rows:
        parsed_date = parse_date_value(row.get(date_column, ""))
        metric_value = to_decimal(row.get(metric_column, ""))
        if parsed_date and metric_value is not None and start <= parsed_date <= end:
            values.append(float(metric_value))
            row_count += 1
    metric = summarize_metric(values)
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "row_count": row_count,
        **metric,
    }


def parse_date_value(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    iso_text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_text).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except ValueError:
            continue
    return None


def bucket_date(value: date, granularity: str) -> date:
    normalized = granularity.lower()
    if normalized == "day":
        return value
    if normalized == "week":
        return value - timedelta(days=value.weekday())
    if normalized == "month":
        return value.replace(day=1)
    raise DataScientistError(f"unsupported granularity: {granularity}")


def format_period(value: date, granularity: str) -> str:
    normalized = granularity.lower()
    if normalized == "month":
        return value.strftime("%Y-%m")
    return value.isoformat()


def parse_period_label(value: str, granularity: str) -> date:
    normalized = granularity.lower()
    if normalized == "month":
        parsed = parse_date_value(f"{value}-01")
    else:
        parsed = parse_date_value(value)
    if not parsed:
        raise DataScientistError(f"invalid period: {value}")
    return parsed


def advance_period(value: date, granularity: str, amount: int) -> date:
    normalized = granularity.lower()
    if normalized == "day":
        return value + timedelta(days=amount)
    if normalized == "week":
        return value + timedelta(weeks=amount)
    if normalized == "month":
        month = value.month - 1 + amount
        year = value.year + month // 12
        month = month % 12 + 1
        return date(year, month, 1)
    raise DataScientistError(f"unsupported granularity: {granularity}")
