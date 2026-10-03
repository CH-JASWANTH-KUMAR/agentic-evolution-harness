"""Accuracy metric calculating mean score across all evaluations."""

from __future__ import annotations

from collections.abc import Sequence

from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection, MetricRegistry


@MetricRegistry.register("accuracy")
class AccuracyMetric:
    """Calculates the average normalized evaluation score across all test cases."""

    name: str = "accuracy"
    direction: MetricDirection = MetricDirection.HIGHER_IS_BETTER

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        if not results:
            return MetricResult(
                name=self.name,
                value=0.0,
                formatted_value="0.00",
                direction=self.direction.value,
                description="Average normalized score across all test cases",
            )

        avg_score = sum(r.average_score for r in results) / len(results)

        return MetricResult(
            name=self.name,
            value=avg_score,
            formatted_value=f"{avg_score:.2f}",
            direction=self.direction.value,
            description="Average normalized score across all test cases",
            details={"sample_size": len(results)},
        )
