#!/usr/bin/env python3
"""Generic runner for N2 auxiliary capabilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runner_support import (
    analyze_codebase,
    build_reproduction_strategy_payload,
    build_contract,
    classify_root_cause,
    execute_specialist_validation_payload_from_args,
    load_fixture,
    load_support_context,
    rank_code_findings_payload,
    review_patch_plan_readiness_payload,
    select_specialist_checks,
    validate_handoff_payload,
    write_output,
)


def run(capability: str) -> int:
    parser = argparse.ArgumentParser(description=f"Run n2-support-agent/{capability}")
    parser.add_argument("--project")
    parser.add_argument("--card", type=int)
    parser.add_argument("--n1-contract")
    parser.add_argument("--codebase-path")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--target-state")
    parser.add_argument("--target-column")
    parser.add_argument("--assign-to")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if capability == "load-support-context":
        payload = load_support_context(args)
        payload.pop("cardMarkdown", None)
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "analyze-code-root-cause":
        context = load_support_context(args)
        payload = analyze_codebase(args.codebase_path, context)
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "classify-root-cause":
        context = load_support_context(args)
        payload = classify_root_cause(context, analyze_codebase(args.codebase_path, context))
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "validate-n1-handoff":
        payload = validate_handoff_payload(load_support_context(args))
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "select-specialist-checks":
        context = load_support_context(args)
        payload = select_specialist_checks(context, classify_root_cause(context, analyze_codebase(args.codebase_path, context)))
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "execute-specialist-validation":
        context = load_support_context(args)
        payload = execute_specialist_validation_payload_from_args(
            args,
            context,
            classify_root_cause(context, analyze_codebase(args.codebase_path, context)),
        )
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "rank-code-findings":
        context = load_support_context(args)
        payload = rank_code_findings_payload(analyze_codebase(args.codebase_path, context))
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "build-reproduction-strategy":
        context = load_support_context(args)
        payload = build_reproduction_strategy_payload(context, analyze_codebase(args.codebase_path, context))
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "review-patch-plan-readiness":
        contract, _ = build_contract(args, write_patch_plan=False)
        payload = review_patch_plan_readiness_payload(contract["patchPlan"], contract["rootCause"], contract["codeAnalysis"])
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability in {"correlate-runtime-evidence", "generate-card-comment", "update-azure-workflow"}:
        contract, _ = build_contract(args, write_patch_plan=False)
        key = {
            "correlate-runtime-evidence": "runtimeCorrelation",
            "generate-card-comment": "artifacts",
            "update-azure-workflow": "azureActions",
        }[capability]
        payload = contract[key]
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    elif capability == "update-n2-card-workflow":
        contract, _ = build_contract(args, write_patch_plan=False)
        payload = {
            "azureActions": contract["azureActions"],
            "targetState": args.target_state,
            "targetColumn": args.target_column,
            "assignTo": args.assign_to,
        }
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)
    else:
        payload = load_fixture(args.fixture)
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_generic(capability, payload)

    write_output(content, args.output)
    return 0


def render_generic(capability: str, payload: Any) -> str:
    return "\n".join(
        [
            f"# N2 {capability.replace('-', ' ').title()}",
            "",
            "```json",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "```",
        ]
    ) + "\n"
