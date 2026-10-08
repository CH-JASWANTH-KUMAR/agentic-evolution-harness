"""Unit tests for the token efficiency metric."""

from __future__ import annotations

from harness.core.agent import AgentOutput, TokenUsage
from harness.core.result import TestCaseResult
from harness.core.testcase import TestCase
from harness.metrics.base import MetricDirection, MetricRegistry
from harness.metrics.token_efficiency import TokenEfficiencyMetric


def _result(
    *,
    passed: bool,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> TestCaseResult:
    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    return TestCaseResult(
        test_case=TestCase(id="test", name="test", input="input"),
        output=AgentOutput(output="output", token_usage=usage),
        passed=passed,
    )


def test_token_efficiency_metric_calculates_token_usage() -> None:
    results = [
        _result(passed=True, prompt_tokens=100, completion_tokens=50),
        _result(passed=True, prompt_tokens=200, completion_tokens=100),
        _result(passed=False, prompt_tokens=300, completion_tokens=150),
    ]

    metric = TokenEfficiencyMetric()
    result = metric.calculate(results)

    assert metric.direction == MetricDirection.LOWER_IS_BETTER
    assert result.value == 450.0
    assert result.formatted_value == "450.0 tokens/pass"
    assert result.details == {
        "total_tokens": 900,
        "prompt_tokens": 600,
        "completion_tokens": 300,
        "passed_tests": 2,
        "tokens_per_pass": 450.0,
        "tokens_per_run": 300.0,
    }


def test_token_efficiency_metric_handles_failed_tests() -> None:
    results = [
        _result(passed=False, prompt_tokens=100, completion_tokens=50),
        _result(passed=False, prompt_tokens=200, completion_tokens=100),
    ]

    result = TokenEfficiencyMetric().calculate(results)

    assert result.value == 0.0
    assert result.formatted_value == "0 tokens/pass"
    assert result.details["passed_tests"] == 0
    assert result.details["tokens_per_pass"] == 0.0
    assert result.details["tokens_per_run"] == 225.0


def test_token_efficiency_metric_handles_empty_results() -> None:
    result = TokenEfficiencyMetric().calculate([])

    assert result.value == 0.0
    assert result.formatted_value == "0 tokens/pass"
    assert result.details == {
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "passed_tests": 0,
        "tokens_per_pass": 0.0,
        "tokens_per_run": 0.0,
    }


def test_token_efficiency_metric_handles_missing_token_usage() -> None:
    missing_usage_result = TestCaseResult(
        test_case=TestCase(id="test", name="test", input="input"),
        output=AgentOutput(output="output"),
        passed=True,
    )

    result = TokenEfficiencyMetric().calculate([missing_usage_result])

    assert result.value == 0.0
    assert result.formatted_value == "0 tokens/pass"
    assert result.details["total_tokens"] == 0
    assert result.details["passed_tests"] == 1
    assert result.details["tokens_per_pass"] == 0.0
    assert result.details["tokens_per_run"] == 0.0


def test_token_efficiency_metric_is_registered() -> None:
    metric = MetricRegistry.get("token_efficiency")

    assert isinstance(metric, TokenEfficiencyMetric)
