"""Reliability metric measuring error-free agent execution rate."""

from __future__ import annotations

from collections.abc import Sequence

from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection, MetricRegistry


@MetricRegistry.register("reliability")
class ReliabilityMetric:
    """Calculates the percentage of test cases that executed without errors or crashes."""

    name: str = "reliability"
    direction: MetricDirection = MetricDirection.HIGHER_IS_BETTER

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        if not results:
            return MetricResult(
                name=self.name,
                value=1.0,
                formatted_value="100.0%",
                direction=self.direction.value,
                description="Percentage of error-free executions",
            )

        total = len(results)
        error_free = sum(1 for r in results if not r.output.is_error)
        rate = error_free / total

        return MetricResult(
            name=self.name,
            value=rate,
            formatted_value=f"{rate * 100.0:.1f}%",
            direction=self.direction.value,
            description="Percentage of error-free executions",
            details={"total": total, "error_free": error_free, "errors": total - error_free},
        )
