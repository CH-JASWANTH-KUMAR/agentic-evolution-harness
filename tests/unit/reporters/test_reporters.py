"""Unit tests for experiment reporters."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from harness.core.agent import AgentOutput
from harness.core.experiment import Experiment, MetricResult
from harness.core.result import EvaluationResult, TestCaseResult
from harness.core.testcase import TestCase
from harness.reporters.console import ConsoleReporter
from harness.reporters.json import JSONReporter
from harness.reporters.markdown import MarkdownReporter


def _sample_experiment() -> Experiment:
    tc = TestCase(id="t1", name="sample_test", input="hi", expected="hello")
    res = TestCaseResult(
        test_case=tc,
        output=AgentOutput(output="hello"),
        evaluations=[EvaluationResult(evaluator="exact_match", score=1.0, passed=True)],
        passed=True,
        duration=0.12,
    )
    return Experiment(
        id="exp-123",
        name="sample-eval",
        results=[res],
        metrics={
            "success_rate": MetricResult(
                name="success_rate",
                value=1.0,
                formatted_value="100.0%",
                direction="higher_is_better",
            )
        },
    )


def test_json_reporter(tmp_path: Path) -> None:
    exp = _sample_experiment()
    out_file = tmp_path / "result.json"
    reporter = JSONReporter()
    text = reporter.report(exp, destination=out_file)

    assert out_file.exists()
    data = json.loads(text)
    assert data["id"] == "exp-123"
    assert data["name"] == "sample-eval"


def test_markdown_reporter(tmp_path: Path) -> None:
    exp = _sample_experiment()
    out_file = tmp_path / "summary.md"
    reporter = MarkdownReporter()
    text = reporter.report(exp, destination=out_file)

    assert out_file.exists()
    assert "# Evaluation Report: sample-eval" in text
    assert "| **Success Rate** | `100.0%` |" in text
    assert "| ✅ Pass | sample_test |" in text


def test_console_reporter() -> None:
    exp = _sample_experiment()
    console = Console(record=True, width=100)
    reporter = ConsoleReporter(console=console)
    reporter.report(exp)
    output = console.export_text()
    assert "Agentic Evolution Harness" in output
    assert "sample_test" in output
    assert "100.0%" in output
