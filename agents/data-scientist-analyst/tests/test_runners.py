#!/usr/bin/env python3
"""Tests for the data-scientist-analyst agent runners."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "ai-devkit"


class DataScientistAnalystRunnersTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def parse_payload(self, result: subprocess.CompletedProcess[str]) -> dict:
        payload = json.loads(result.stdout)
        if "stdout" in payload:
            return json.loads(payload["stdout"])
        return payload

    def write_customer_csv(self, root: Path) -> Path:
        source = root / "customers.csv"
        source.write_text(
            "\n".join(
                [
                    "cpf,name,status,amount,created_at,email",
                    "12345678909,Ana,active,100.50,2026-06-01,ana@example.com",
                    "11144477735,Beto,inactive,200.00,2026-06-02,beto@example.com",
                    "12345678909,Ana,active,100.50,2026-06-01,ana@example.com",
                    "00000000000,Caio,active,,2026-06-03,caio@example.com",
                ]
            ),
            encoding="utf-8",
        )
        return source

    def write_analytics_csv(self, root: Path) -> Path:
        source = root / "analytics.csv"
        source.write_text(
            "\n".join(
                [
                    "id,segment,age,score,income,converted",
                    "1,A,20,40,100,0",
                    "2,A,30,60,150,1",
                    "3,B,40,80,200,1",
                    "4,B,50,100,250,1",
                    "5,C,60,120,10000,0",
                ]
            ),
            encoding="utf-8",
        )
        return source

    def write_time_series_csv(self, root: Path) -> Path:
        source = root / "events.csv"
        source.write_text(
            "\n".join(
                [
                    "customer_id,signup_date,event_date,amount,converted",
                    "1,2026-01-01,2026-01-01,10,1",
                    "1,2026-01-01,2026-01-02,12,0",
                    "2,2026-01-02,2026-01-02,14,1",
                    "2,2026-01-02,2026-01-03,16,1",
                    "3,2026-01-03,2026-01-03,100,0",
                    "3,2026-01-03,2026-01-04,18,1",
                    "4,2026-01-04,2026-01-04,20,0",
                ]
            ),
            encoding="utf-8",
        )
        return source

    def write_experiment_csv(self, root: Path) -> Path:
        source = root / "experiment.csv"
        source.write_text(
            "\n".join(
                [
                    "user_id,variant,revenue,converted",
                    "1,control,10,0",
                    "2,control,12,0",
                    "3,control,14,1",
                    "4,control,16,1",
                    "5,treatment,18,1",
                    "6,treatment,20,1",
                    "7,treatment,22,1",
                    "8,treatment,24,1",
                ]
            ),
            encoding="utf-8",
        )
        return source

    def test_agent_is_listed_with_mvp_capabilities(self) -> None:
        agents_result = self.run_cli("--json", "agents")
        self.assertEqual(agents_result.returncode, 0, agents_result.stderr)
        agents = {item["id"] for item in json.loads(agents_result.stdout)["items"]}
        self.assertIn("data-scientist-analyst", agents)

        capabilities_result = self.run_cli(
            "--json",
            "capabilities",
            "data-scientist-analyst",
        )
        self.assertEqual(capabilities_result.returncode, 0, capabilities_result.stderr)
        capabilities = {
            item["id"].split(".")[-1]
            for item in json.loads(capabilities_result.stdout)["items"]
        }
        self.assertGreaterEqual(
            capabilities,
            {
                "ingest-dataset",
                "inspect-dataset-schema",
                "profile-dataset",
                "detect-sensitive-data",
                "reconcile-spreadsheets",
                "generate-reconciliation-report",
                "generate-data-report",
                "analyze-sql-source",
                "run-exploratory-analysis",
                "detect-outliers",
                "analyze-correlation",
                "segment-data",
                "analyze-time-series",
                "compare-periods",
                "analyze-cohorts",
                "detect-anomalies",
                "forecast-series",
                "test-hypothesis",
                "calculate-confidence-intervals",
                "calculate-sample-size",
                "measure-effect-size",
                "explain-statistical-result",
            },
        )

    def test_profile_dataset_reports_schema_quality_and_sensitive_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_customer_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "profile-dataset",
                "--source",
                str(source),
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["dataset"]["row_count"], 4)
        self.assertEqual(payload["dataset"]["column_count"], 6)
        self.assertEqual(payload["quality"]["duplicate_row_count"], 1)
        self.assertIn("cpf", payload["schema"]["probable_keys"])
        self.assertIn("cpf", payload["sensitive_data"]["columns"])
        self.assertEqual(payload["columns"]["amount"]["missing_count"], 1)
        self.assertEqual(payload["columns"]["amount"]["inferred_type"], "number")

    def test_reconcile_spreadsheets_matches_and_explains_differences(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            left = root / "erp.csv"
            right = root / "bank.csv"
            left.write_text(
                "\n".join(
                    [
                        "id,cpf,amount,status",
                        "1,12345678909,100.00,paid",
                        "2,11144477735,200.00,pending",
                        "3,55566677788,50.00,paid",
                    ]
                ),
                encoding="utf-8",
            )
            right.write_text(
                "\n".join(
                    [
                        "id,cpf,amount,status",
                        "1,12345678909,100.01,paid",
                        "2,11144477735,250.00,paid",
                        "4,99988877766,10.00,paid",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "reconcile-spreadsheets",
                "--left",
                str(left),
                "--right",
                str(right),
                "--key",
                "id",
                "--compare-columns",
                "amount,status",
                "--numeric-tolerance",
                "0.02",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["summary"]["matched_count"], 1)
        self.assertEqual(payload["summary"]["mismatched_count"], 1)
        self.assertEqual(payload["summary"]["missing_right_count"], 1)
        self.assertEqual(payload["summary"]["missing_left_count"], 1)
        mismatch = payload["mismatched"][0]
        self.assertEqual(mismatch["key"], "2")
        fields = {item["column"] for item in mismatch["differences"]}
        self.assertEqual(fields, {"amount", "status"})

    def test_generate_data_report_writes_markdown_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = self.write_customer_csv(root)
            output = root / "report.md"
            result = self.run_cli(
                "run",
                "data-scientist-analyst",
                "generate-data-report",
                "--source",
                str(source),
                "--output",
                str(output),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            content = output.read_text(encoding="utf-8")

        self.assertIn("# Relatorio de Dados", content)
        self.assertIn("Linhas: 4", content)
        self.assertIn("Dados sensiveis", content)

    def test_detect_sensitive_data_does_not_classify_phone_as_cpf(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "contacts.csv"
            source.write_text(
                "id,email,phone\n1,a@example.com,11999998888\n",
                encoding="utf-8",
            )
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "detect-sensitive-data",
                "--source",
                str(source),
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["sensitive_data"]["columns"]["phone"], ["phone"])

    def test_detect_outliers_reports_iqr_outlier(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_analytics_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "detect-outliers",
                "--source",
                str(source),
                "--columns",
                "income",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        income = payload["columns"]["income"]
        self.assertEqual(income["outlier_count"], 1)
        self.assertEqual(income["outliers"][0]["row_number"], 5)
        self.assertEqual(income["outliers"][0]["value"], 10000.0)

    def test_analyze_correlation_ranks_numeric_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_analytics_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "analyze-correlation",
                "--source",
                str(source),
                "--columns",
                "age,score,income",
                "--target-column",
                "score",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        top_pair = payload["top_correlations"][0]
        self.assertEqual({top_pair["left"], top_pair["right"]}, {"age", "score"})
        self.assertAlmostEqual(top_pair["correlation"], 1.0)
        target_pairs = {
            item["column"]: item["correlation"]
            for item in payload["target_correlations"]
        }
        self.assertAlmostEqual(target_pairs["age"], 1.0)

    def test_segment_data_summarizes_category_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_analytics_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "segment-data",
                "--source",
                str(source),
                "--segment-column",
                "segment",
                "--metric-column",
                "converted",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        segments = {item["segment"]: item for item in payload["segments"]}
        self.assertEqual(segments["A"]["row_count"], 2)
        self.assertEqual(segments["A"]["metric"]["sum"], 1.0)
        self.assertEqual(segments["B"]["metric"]["mean"], 1.0)
        self.assertEqual(payload["summary"]["segment_count"], 3)

    def test_run_exploratory_analysis_combines_phase_one_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_analytics_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "run-exploratory-analysis",
                "--source",
                str(source),
                "--target-column",
                "converted",
                "--segment-column",
                "segment",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["dataset"]["row_count"], 5)
        self.assertIn("income", payload["outliers"]["columns"])
        self.assertTrue(payload["correlations"]["top_correlations"])
        self.assertEqual(payload["segments"]["summary"]["segment_count"], 3)
        self.assertTrue(payload["hypotheses"])

    def test_analyze_time_series_aggregates_metric_by_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_time_series_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "analyze-time-series",
                "--source",
                str(source),
                "--date-column",
                "event_date",
                "--metric-column",
                "amount",
                "--granularity",
                "day",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["summary"]["period_count"], 4)
        self.assertEqual(payload["series"][0]["period"], "2026-01-01")
        self.assertEqual(payload["series"][0]["sum"], 10.0)
        self.assertEqual(payload["series"][2]["sum"], 116.0)
        self.assertEqual(payload["trend"]["direction"], "up")

    def test_compare_periods_reports_delta_between_date_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_time_series_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "compare-periods",
                "--source",
                str(source),
                "--date-column",
                "event_date",
                "--metric-column",
                "amount",
                "--baseline-start",
                "2026-01-01",
                "--baseline-end",
                "2026-01-02",
                "--comparison-start",
                "2026-01-03",
                "--comparison-end",
                "2026-01-04",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["baseline"]["sum"], 36.0)
        self.assertEqual(payload["comparison"]["sum"], 154.0)
        self.assertEqual(payload["delta"]["absolute"], 118.0)
        self.assertAlmostEqual(payload["delta"]["percent"], 327.777778)

    def test_analyze_cohorts_groups_by_signup_age(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_time_series_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "analyze-cohorts",
                "--source",
                str(source),
                "--cohort-column",
                "signup_date",
                "--event-date-column",
                "event_date",
                "--metric-column",
                "converted",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["summary"]["cohort_count"], 4)
        first = payload["cohorts"][0]
        self.assertEqual(first["cohort"], "2026-01-01")
        self.assertEqual(first["periods"]["0"]["row_count"], 1)
        self.assertEqual(first["periods"]["0"]["metric"]["sum"], 1.0)
        self.assertEqual(first["periods"]["1"]["metric"]["sum"], 0.0)

    def test_detect_anomalies_flags_spike_in_time_series(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_time_series_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "detect-anomalies",
                "--source",
                str(source),
                "--date-column",
                "event_date",
                "--metric-column",
                "amount",
                "--threshold",
                "1.0",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        periods = [item["period"] for item in payload["anomalies"]]
        self.assertIn("2026-01-03", periods)

    def test_forecast_series_projects_next_periods(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_time_series_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "forecast-series",
                "--source",
                str(source),
                "--date-column",
                "event_date",
                "--metric-column",
                "amount",
                "--periods",
                "2",
                "--window",
                "2",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(len(payload["forecast"]), 2)
        self.assertEqual(payload["forecast"][0]["period"], "2026-01-05")
        self.assertEqual(payload["forecast"][0]["forecast"], 77.0)
        self.assertEqual(payload["method"], "moving_average")

    def test_test_hypothesis_compares_group_means(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_experiment_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "test-hypothesis",
                "--source",
                str(source),
                "--test-type",
                "mean-difference",
                "--group-column",
                "variant",
                "--group-a",
                "control",
                "--group-b",
                "treatment",
                "--metric-column",
                "revenue",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["test_type"], "mean-difference")
        self.assertEqual(payload["groups"]["control"]["mean"], 13.0)
        self.assertEqual(payload["groups"]["treatment"]["mean"], 21.0)
        self.assertEqual(payload["difference"], 8.0)
        self.assertTrue(payload["p_value"] < 0.01)
        self.assertTrue(payload["significant"])

    def test_calculate_confidence_intervals_reports_mean_interval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_experiment_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "calculate-confidence-intervals",
                "--source",
                str(source),
                "--metric-column",
                "revenue",
                "--confidence",
                "0.95",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["metric_column"], "revenue")
        self.assertEqual(payload["mean"], 17.0)
        self.assertEqual(payload["sample_size"], 8)
        self.assertAlmostEqual(payload["interval"]["lower"], 13.953, places=3)
        self.assertAlmostEqual(payload["interval"]["upper"], 20.047, places=3)

    def test_calculate_sample_size_for_two_proportions(self) -> None:
        result = self.run_cli(
            "--json",
            "run",
            "data-scientist-analyst",
            "calculate-sample-size",
            "--baseline-rate",
            "0.5",
            "--minimum-detectable-effect",
            "0.1",
            "--alpha",
            "0.05",
            "--power",
            "0.8",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["method"], "two_proportions_normal_approx")
        self.assertEqual(payload["sample_size_per_group"], 385)
        self.assertEqual(payload["total_sample_size"], 770)

    def test_measure_effect_size_reports_cohens_d(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = self.write_experiment_csv(Path(tmpdir))
            result = self.run_cli(
                "--json",
                "run",
                "data-scientist-analyst",
                "measure-effect-size",
                "--source",
                str(source),
                "--group-column",
                "variant",
                "--group-a",
                "control",
                "--group-b",
                "treatment",
                "--metric-column",
                "revenue",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertEqual(payload["method"], "cohens_d")
        self.assertAlmostEqual(payload["effect_size"], 3.098387, places=6)
        self.assertEqual(payload["magnitude"], "large")

    def test_explain_statistical_result_interprets_significance(self) -> None:
        result = self.run_cli(
            "--json",
            "run",
            "data-scientist-analyst",
            "explain-statistical-result",
            "--p-value",
            "0.01",
            "--alpha",
            "0.05",
            "--effect-size",
            "0.8",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.parse_payload(result)
        self.assertTrue(payload["significant"])
        self.assertEqual(payload["effect_magnitude"], "large")
        self.assertIn("estatisticamente significativo", payload["executive_summary"])


if __name__ == "__main__":
    unittest.main()
