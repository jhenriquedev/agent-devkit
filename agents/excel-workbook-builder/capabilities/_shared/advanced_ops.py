"""Advanced operation runners for excel-workbook-builder phase 2/3."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from workbook_support import (
    apply_formula_plan,
    fill_workbook_from_dataset,
    generate_workbook_from_dataset,
    inspect_xlsx,
    load_tabular_file,
)


def run(operation: str) -> int:
    try:
        if operation == "create-summary-dashboard":
            return create_summary_dashboard()
        if operation == "create-pivot-summary":
            return create_pivot_summary()
        if operation == "validate-reconciliation-rules":
            return validate_reconciliation_rules()
        if operation == "explain-reconciliation-differences":
            return explain_reconciliation_differences()
        if operation == "generate-reconciliation-report":
            return generate_reconciliation_report()
        if operation == "create-adjustment-suggestions":
            return create_adjustment_suggestions()
        if operation == "export-workbook-artifacts":
            return export_workbook_artifacts()
        if operation in {"update-existing-workbook", "refresh-workbook-data"}:
            return refresh_workbook_data(operation)
        if operation == "run-workbook-operation":
            return run_workbook_operation()
        if operation == "add-formulas-and-validations":
            return add_formulas_and_validations()
        if operation == "refine-generated-workbook":
            return copy_workbook_operation(operation)
        raise ValueError(f"unsupported operation: {operation}")
    except Exception as exc:  # pragma: no cover - exercised through CLI tests
        print(f"error: {exc}")
        return 1


def create_summary_dashboard() -> int:
    parser = argparse.ArgumentParser(description="Create summary dashboard workbook")
    parser.add_argument("--metrics")
    parser.add_argument("--input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Dashboard Executivo")
    args = parser.parse_args()
    rows = []
    if args.metrics:
        raw = json.loads(Path(args.metrics).expanduser().resolve().read_text(encoding="utf-8"))
        rows = raw.get("metrics", raw if isinstance(raw, list) else [])
    elif args.input:
        dataset = load_tabular_file(Path(args.input).expanduser().resolve())
        rows = [{"metric": "rows", "value": dataset["row_count"]}, {"metric": "columns", "value": len(dataset["columns"])}]
    dataset = {"source": args.metrics or args.input or "", "columns": ["metric", "value"], "rows": rows}
    generate_workbook_from_dataset(dataset, Path(args.output).expanduser().resolve(), title=args.title)
    print(f"Dashboard gerado: {Path(args.output).expanduser().resolve()}")
    return 0


def create_pivot_summary() -> int:
    parser = argparse.ArgumentParser(description="Create pivot-style summary workbook")
    parser.add_argument("--input", required=True)
    parser.add_argument("--group-by", action="append", default=[])
    parser.add_argument("--value", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    dataset = load_tabular_file(Path(args.input).expanduser().resolve())
    group_by = expand_csv(args.group_by)
    values = expand_csv(args.value)
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in dataset["rows"]:
        key = tuple(row.get(column) for column in group_by)
        item = grouped.setdefault(key, {column: key[index] for index, column in enumerate(group_by)})
        item["count"] = item.get("count", 0) + 1
        for column in values:
            item[f"sum_{column}"] = item.get(f"sum_{column}", 0) + numeric(row.get(column))
    rows = list(grouped.values())
    columns = group_by + ["count"] + [f"sum_{column}" for column in values]
    generate_workbook_from_dataset(
        {"source": dataset.get("source", ""), "columns": columns, "rows": rows},
        Path(args.output).expanduser().resolve(),
        title="Resumo Pivot",
    )
    print(f"Resumo pivot gerado: {Path(args.output).expanduser().resolve()}")
    return 0


def validate_reconciliation_rules() -> int:
    parser = argparse.ArgumentParser(description="Validate reconciliation rules")
    parser.add_argument("--rules")
    parser.add_argument("--key")
    parser.add_argument("--compare-column", action="append", default=[])
    parser.add_argument("--tolerance", type=float, default=0.0)
    parser.add_argument("--output")
    args = parser.parse_args()
    rules = {}
    if args.rules:
        rules = json.loads(Path(args.rules).expanduser().resolve().read_text(encoding="utf-8"))
    keys = expand_csv([rules.get("key", ""), args.key or ""])
    compare_columns = expand_csv((rules.get("compare_columns") or []) + args.compare_column)
    errors = []
    if not keys:
        errors.append("Missing reconciliation key.")
    if not compare_columns:
        errors.append("Missing compare columns.")
    if args.tolerance < 0:
        errors.append("Tolerance cannot be negative.")
    markdown = "# Reconciliation Rules Validation\n\n"
    markdown += f"- Status: {'fail' if errors else 'pass'}\n"
    markdown += f"- Keys: {', '.join(keys) if keys else '-'}\n"
    markdown += f"- Compare columns: {', '.join(compare_columns) if compare_columns else '-'}\n"
    markdown += f"- Tolerance: {args.tolerance}\n\n## Errors\n\n"
    markdown += "\n".join(f"- {item}" for item in errors) if errors else "- None"
    markdown += "\n"
    write_or_print(markdown, args.output)
    return 1 if errors else 0


def explain_reconciliation_differences() -> int:
    parser = argparse.ArgumentParser(description="Explain reconciliation differences")
    parser.add_argument("--summary", "--reconciliation-summary", dest="summary", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    summary = json.loads(Path(args.summary).expanduser().resolve().read_text(encoding="utf-8"))
    markdown = "\n".join(
        [
            "# Reconciliation Difference Explanation",
            "",
            f"- Matched: {summary.get('matched', 0)}",
            f"- Different: {summary.get('different', 0)}",
            f"- Left only: {summary.get('left_only', 0)}",
            f"- Right only: {summary.get('right_only', 0)}",
            "",
            "## Interpretation",
            "",
            "- `different` indica chaves presentes nos dois lados com valores divergentes.",
            "- `left_only` indica registros ausentes na base direita.",
            "- `right_only` indica registros ausentes na base esquerda.",
        ]
    ) + "\n"
    write_or_print(markdown, args.output)
    return 0


def generate_reconciliation_report() -> int:
    parser = argparse.ArgumentParser(description="Generate reconciliation report workbook")
    parser.add_argument("--reconciliation-data")
    parser.add_argument("--summary")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = {}
    if args.reconciliation_data:
        payload = json.loads(Path(args.reconciliation_data).expanduser().resolve().read_text(encoding="utf-8"))
    elif args.summary:
        payload = {"summary": json.loads(Path(args.summary).expanduser().resolve().read_text(encoding="utf-8"))}
    summary = payload.get("summary", payload)
    rows = [{"metric": key, "value": value} for key, value in summary.items()]
    generate_workbook_from_dataset(
        {"source": args.reconciliation_data or args.summary or "", "columns": ["metric", "value"], "rows": rows},
        Path(args.output).expanduser().resolve(),
        title="Relatorio de Conciliacao",
    )
    print(f"Relatorio de conciliacao gerado: {Path(args.output).expanduser().resolve()}")
    return 0


def create_adjustment_suggestions() -> int:
    parser = argparse.ArgumentParser(description="Create adjustment suggestions workbook")
    parser.add_argument("--reconciliation-data", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.reconciliation_data).expanduser().resolve().read_text(encoding="utf-8"))
    rows = [
        {
            "reconciliation_key": row.get("reconciliation_key"),
            "suggestion": "Review difference before posting adjustment",
            "status": row.get("status"),
        }
        for row in payload.get("rows", [])
        if row.get("status") == "different"
    ]
    generate_workbook_from_dataset(
        {"source": args.reconciliation_data, "columns": ["reconciliation_key", "suggestion", "status"], "rows": rows},
        Path(args.output).expanduser().resolve(),
        title="Sugestoes de Ajuste",
    )
    print(f"Sugestoes geradas: {Path(args.output).expanduser().resolve()}")
    return 0


def export_workbook_artifacts() -> int:
    parser = argparse.ArgumentParser(description="Export final workbook artifacts")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--include-review", action="store_true")
    args = parser.parse_args()
    workbook = Path(args.workbook).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / workbook.name
    shutil.copyfile(workbook, target)
    if args.include_review:
        review = inspect_xlsx(workbook)
        (output_dir / "review.md").write_text(
            f"# Workbook Review\n\n- Worksheets: {review['worksheet_count']}\n- Formula errors: {', '.join(review['formula_errors']) if review['formula_errors'] else '-'}\n",
            encoding="utf-8",
        )
    print(f"Artefatos exportados: {target}")
    return 0


def copy_workbook_operation(operation: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run {operation}")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--output")
    parser.add_argument("--feedback")
    parser.add_argument("--operation")
    parser.add_argument("--input")
    args, _ = parser.parse_known_args()
    workbook = Path(args.workbook).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else workbook.with_name(f"{workbook.stem}-{operation}.xlsx")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(workbook, output)
    print(f"Workbook gerado: {output}")
    return 0


def refresh_workbook_data(operation: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run {operation}")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sheet", default="Data")
    parser.add_argument("--title", default="Workbook Atualizado")
    args = parser.parse_args()
    workbook = Path(args.workbook).expanduser().resolve()
    if not workbook.exists():
        raise ValueError(f"workbook not found: {workbook}")
    dataset = load_tabular_file(Path(args.input).expanduser().resolve())
    fill_workbook_from_dataset(
        workbook,
        dataset,
        Path(args.output).expanduser().resolve(),
        data_sheet=args.sheet,
    )
    print(f"Workbook gerado: {Path(args.output).expanduser().resolve()}")
    return 0


def run_workbook_operation() -> int:
    parser = argparse.ArgumentParser(description="Run workbook operation")
    parser.add_argument("--workbook")
    parser.add_argument("--input")
    parser.add_argument("--operation", required=True)
    parser.add_argument("--group-by", action="append", default=[])
    parser.add_argument("--value", action="append", default=[])
    parser.add_argument("--sort-by")
    parser.add_argument("--descending", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = args.input or args.workbook
    if not source:
        raise ValueError("--input or --workbook is required")
    dataset = load_tabular_file(Path(source).expanduser().resolve())
    operation = args.operation.strip().lower()
    if operation == "aggregate":
        result = aggregate_dataset(dataset, expand_csv(args.group_by), expand_csv(args.value))
        title = "Operacao Aggregate"
    elif operation == "sort":
        result = sort_dataset(dataset, args.sort_by, args.descending)
        title = "Operacao Sort"
    else:
        raise ValueError(f"unsupported operation: {args.operation}")
    generate_workbook_from_dataset(result, Path(args.output).expanduser().resolve(), title=title)
    print(f"Workbook gerado: {Path(args.output).expanduser().resolve()}")
    return 0


def aggregate_dataset(dataset: dict[str, Any], group_by: list[str], values: list[str]) -> dict[str, Any]:
    if not group_by:
        raise ValueError("--group-by is required for aggregate")
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in dataset["rows"]:
        key = tuple(row.get(column) for column in group_by)
        item = grouped.setdefault(key, {column: key[index] for index, column in enumerate(group_by)})
        item["count"] = item.get("count", 0) + 1
        for column in values:
            item[f"sum_{column}"] = item.get(f"sum_{column}", 0) + numeric(row.get(column))
    columns = group_by + ["count"] + [f"sum_{column}" for column in values]
    return {"source": dataset.get("source", ""), "columns": columns, "rows": list(grouped.values())}


def sort_dataset(dataset: dict[str, Any], sort_by: str | None, descending: bool) -> dict[str, Any]:
    if not sort_by:
        raise ValueError("--sort-by is required for sort")
    rows = sorted(dataset["rows"], key=lambda row: row.get(sort_by), reverse=descending)
    return {"source": dataset.get("source", ""), "columns": dataset["columns"], "rows": rows}


def add_formulas_and_validations() -> int:
    parser = argparse.ArgumentParser(description="Add formulas and validations")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--formula-plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    apply_formula_plan(
        Path(args.workbook).expanduser().resolve(),
        Path(args.formula_plan).expanduser().resolve(),
        Path(args.output).expanduser().resolve(),
    )
    print(f"Workbook gerado: {Path(args.output).expanduser().resolve()}")
    return 0


def expand_csv(values: list[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        if isinstance(value, list):
            result.extend(expand_csv(value))
            continue
        for item in str(value or "").split(","):
            cleaned = item.strip()
            if cleaned and cleaned not in result:
                result.append(cleaned)
    return result


def numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def write_or_print(markdown: str, output: str | None) -> None:
    if output:
        target = Path(output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
