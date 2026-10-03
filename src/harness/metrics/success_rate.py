"""Success rate metric calculation."""

from __future__ import annotations

from collections.abc import Sequence

from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection, MetricRegistry


@MetricRegistry.register("success_rate")
class SuccessRateMetric:
    """Calculates the percentage of test cases that passed all required evaluators."""

    name: str = "success_rate"
    direction: MetricDirection = MetricDirection.HIGHER_IS_BETTER

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        if not results:
            return MetricResult(
                name=self.name,
                value=0.0,
                formatted_value="0.0%",
                direction=self.direction.value,
                description="Percentage of passed test cases",
                details={"total": 0, "passed": 0},
            )

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        rate = passed / total
        pct = rate * 100.0

        return MetricResult(
            name=self.name,
            value=rate,
            formatted_value=f"{pct:.1f}%",
            direction=self.direction.value,
            description="Percentage of passed test cases",
            details={"total": total, "passed": passed, "failed": total - passed},
        )
