"""Unit tests for experiment comparator and regression detector."""

from __future__ import annotations

from harness.comparison.comparator import ExperimentComparator
from harness.comparison.regression import RegressionDetector
from harness.core.agent import AgentOutput
from harness.core.experiment import Experiment, MetricResult
from harness.core.result import TestCaseResult
from harness.core.testcase import TestCase


def _build_test_exp(
    name: str,
    success_rate: float,
    latency: float,
    cost: float,
    test_outcomes: dict[str, bool],
) -> Experiment:
    results: list[TestCaseResult] = []
    for tc_name, passed in test_outcomes.items():
        tc = TestCase(id=tc_name, name=tc_name, input=tc_name)
        results.append(
            TestCaseResult(
                test_case=tc,
                output=AgentOutput(output="ok"),
                passed=passed,
                duration=latency,
            )
        )

    metrics = {
        "success_rate": MetricResult(
            name="success_rate",
            value=success_rate,
            formatted_value=f"{success_rate * 100:.1f}%",
            direction="higher_is_better",
        ),
        "latency": MetricResult(
            name="latency",
            value=latency,
            formatted_value=f"{latency:.2f}s",
            direction="lower_is_better",
        ),
        "cost": MetricResult(
            name="cost",
            value=cost,
            formatted_value=f"${cost:.4f}",
            direction="lower_is_better",
        ),
    }

    return Experiment(
        id=name,
        name=name,
        results=results,
        metrics=metrics,
    )


def test_experiment_comparator_improvements_and_regressions() -> None:
    exp_v1 = _build_test_exp(
        "v1",
        success_rate=0.70,
        latency=2.0,
        cost=0.010,
        test_outcomes={"test_a": True, "test_b": False},
    )
    exp_v2 = _build_test_exp(
        "v2",
        success_rate=0.85,
        latency=1.5,
        cost=0.012,
        test_outcomes={"test_a": True, "test_b": True},
    )

    comparison = ExperimentComparator.compare(exp_v1, exp_v2)

    # Success rate improved
    sr_delta = comparison.deltas["success_rate"]
    assert sr_delta.is_improvement
    assert not sr_delta.is_regression
    assert abs(sr_delta.delta - 0.15) < 1e-6

    # Latency improved (dropped from 2.0 to 1.5)
    lat_delta = comparison.deltas["latency"]
    assert lat_delta.is_improvement
    assert not lat_delta.is_regression
    assert abs(lat_delta.delta - (-0.5)) < 1e-6

    # Cost regressed (increased from 0.010 to 0.012)
    cost_delta = comparison.deltas["cost"]
    assert cost_delta.is_regression
    assert not cost_delta.is_improvement

    # Test transitions
    assert "test_b" in comparison.newly_passed_tests
    assert len(comparison.newly_failed_tests) == 0


def test_regression_detector_violations() -> None:
    exp = _build_test_exp(
        "v1",
        success_rate=0.65,
        latency=3.5,
        cost=0.005,
        test_outcomes={"test_a": True},
    )

    thresholds = {
        "success_rate": {"minimum": 0.80},
        "latency": {"maximum": 2.0},
    }

    report = RegressionDetector.check_thresholds(exp, thresholds)
    assert not report.passed
    assert len(report.violations) == 2

    # Compliant experiment
    exp_good = _build_test_exp(
        "v2",
        success_rate=0.95,
        latency=1.2,
        cost=0.005,
        test_outcomes={"test_a": True},
    )
    report_good = RegressionDetector.check_thresholds(exp_good, thresholds)
    assert report_good.passed
    assert len(report_good.violations) == 0
