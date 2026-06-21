#!/usr/bin/env python3
"""CLI for the AWS CloudWatch Logs repository."""

from __future__ import annotations

import argparse
import json
import sys

from cloudwatch_repository import CloudWatchRepository, CloudWatchRepositoryError


def main() -> int:
    parser = argparse.ArgumentParser(description="AWS CloudWatch Logs integration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-log-groups")
    list_parser.add_argument("--region")
    list_parser.add_argument("--log-group-prefix")
    list_parser.add_argument("--limit", type=int, default=50)

    filter_parser = subparsers.add_parser("filter-log-events")
    filter_parser.add_argument("--region")
    filter_parser.add_argument("--log-group", required=True)
    filter_parser.add_argument("--start-time", required=True)
    filter_parser.add_argument("--end-time", required=True)
    filter_parser.add_argument("--filter-pattern")
    filter_parser.add_argument("--log-stream-prefix")
    filter_parser.add_argument("--limit", type=int, default=100)

    query_parser = subparsers.add_parser("start-logs-insights-query")
    query_parser.add_argument("--region")
    query_parser.add_argument("--log-group", required=True)
    query_parser.add_argument("--start-time", required=True)
    query_parser.add_argument("--end-time", required=True)
    query_parser.add_argument("--query", required=True)
    query_parser.add_argument("--limit", type=int, default=100)

    results_parser = subparsers.add_parser("get-logs-insights-query-results")
    results_parser.add_argument("--region")
    results_parser.add_argument("--query-id", required=True)

    streams_parser = subparsers.add_parser("describe-log-streams")
    streams_parser.add_argument("--region")
    streams_parser.add_argument("--log-group", required=True)
    streams_parser.add_argument("--log-stream-prefix")
    streams_parser.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()

    try:
        repo = CloudWatchRepository()
        result = run_command(repo, args)
    except CloudWatchRepositoryError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_command(repo: CloudWatchRepository, args: argparse.Namespace) -> dict:
    if args.command == "list-log-groups":
        return repo.list_log_groups(
            region=args.region,
            log_group_prefix=args.log_group_prefix,
            limit=args.limit,
        )
    if args.command == "filter-log-events":
        return repo.filter_log_events(
            region=args.region,
            log_group=args.log_group,
            start_time=args.start_time,
            end_time=args.end_time,
            filter_pattern=args.filter_pattern,
            log_stream_prefix=args.log_stream_prefix,
            limit=args.limit,
        )
    if args.command == "start-logs-insights-query":
        return repo.start_logs_insights_query(
            region=args.region,
            log_group=args.log_group,
            start_time=args.start_time,
            end_time=args.end_time,
            query=args.query,
            limit=args.limit,
        )
    if args.command == "get-logs-insights-query-results":
        return repo.get_logs_insights_query_results(
            region=args.region,
            query_id=args.query_id,
        )
    if args.command == "describe-log-streams":
        return repo.describe_log_streams(
            region=args.region,
            log_group=args.log_group,
            log_stream_prefix=args.log_stream_prefix,
            limit=args.limit,
        )
    raise CloudWatchRepositoryError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
