"""Token consumption efficiency metric for agent evaluations."""

from __future__ import annotations

from collections.abc import Sequence

from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection, MetricRegistry


@MetricRegistry.register("token_efficiency")
class TokenEfficiencyMetric:
    """Calculates token consumption per passed test case and per test run."""

    name: str = "token_efficiency"
    direction: MetricDirection = MetricDirection.LOWER_IS_BETTER

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0

        for result in results:
            token_usage = result.output.token_usage
            if token_usage is None:
                continue
            total_tokens += token_usage.total_tokens
            prompt_tokens += token_usage.prompt_tokens
            completion_tokens += token_usage.completion_tokens

        passed_tests = sum(1 for result in results if result.passed)
        tokens_per_pass = total_tokens / passed_tests if passed_tests else 0.0
        tokens_per_run = total_tokens / len(results) if results else 0.0
        formatted_value = (
            f"{tokens_per_pass:.1f} tokens/pass" if tokens_per_pass else "0 tokens/pass"
        )

        return MetricResult(
            name=self.name,
            value=tokens_per_pass,
            formatted_value=formatted_value,
            direction=self.direction.value,
            description="Average token consumption per passed test case",
            details={
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "passed_tests": passed_tests,
                "tokens_per_pass": tokens_per_pass,
                "tokens_per_run": tokens_per_run,
            },
        )
