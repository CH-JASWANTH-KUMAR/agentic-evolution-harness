"""Unit tests for built-in metrics."""

from __future__ import annotations

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult, TestCaseResult
from harness.core.testcase import TestCase
from harness.metrics.accuracy import AccuracyMetric
from harness.metrics.cost import CostMetric
from harness.metrics.latency import LatencyMetric
from harness.metrics.reliability import ReliabilityMetric
from harness.metrics.success_rate import SuccessRateMetric


def _make_test_result(
    passed: bool,
    score: float = 1.0,
    latency: float = 0.5,
    cost: float = 0.001,
    is_error: bool = False,
) -> TestCaseResult:
    tc = TestCase(id="t1", name="t1", input="in")
    out = AgentOutput(
        output="out",
        latency=latency,
        cost=cost,
        error="Crash" if is_error else None,
    )
    return TestCaseResult(
        test_case=tc,
        output=out,
        evaluations=[EvaluationResult(evaluator="test", score=score, passed=passed)],
        passed=passed,
        duration=latency,
    )


def test_success_rate_metric() -> None:
    metric = SuccessRateMetric()
    results = [
        _make_test_result(passed=True),
        _make_test_result(passed=True),
        _make_test_result(passed=False),
        _make_test_result(passed=True),
    ]
    res = metric.calculate(results)
    assert res.value == 0.75
    assert res.formatted_value == "75.0%"

    empty_res = metric.calculate([])
    assert empty_res.value == 0.0


def test_accuracy_metric() -> None:
    metric = AccuracyMetric()
    results = [
        _make_test_result(passed=True, score=1.0),
        _make_test_result(passed=False, score=0.5),
    ]
    res = metric.calculate(results)
    assert res.value == 0.75
    assert res.formatted_value == "0.75"


def test_latency_metric() -> None:
    metric = LatencyMetric()
    results = [
        _make_test_result(passed=True, latency=1.0),
        _make_test_result(passed=True, latency=2.0),
    ]
    res = metric.calculate(results)
    assert res.value == 1.5
    assert res.formatted_value == "1.50s"


def test_cost_metric() -> None:
    metric = CostMetric()
    results = [
        _make_test_result(passed=True, cost=0.005),
        _make_test_result(passed=True, cost=0.003),
    ]
    res = metric.calculate(results)
    assert abs(res.value - 0.008) < 1e-6
    assert "$0.0080" in res.formatted_value


def test_reliability_metric() -> None:
    metric = ReliabilityMetric()
    results = [
        _make_test_result(passed=True, is_error=False),
        _make_test_result(passed=False, is_error=True),
        _make_test_result(passed=True, is_error=False),
        _make_test_result(passed=True, is_error=False),
    ]
    res = metric.calculate(results)
    assert res.value == 0.75
    assert res.formatted_value == "75.0%"
