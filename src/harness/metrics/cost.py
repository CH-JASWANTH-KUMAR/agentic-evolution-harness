"""Cost metric tracking total monetary expenditure of agent executions."""

from __future__ import annotations

from collections.abc import Sequence

from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection, MetricRegistry


@MetricRegistry.register("cost")
class CostMetric:
    """Calculates total and average monetary cost across test runs."""

    name: str = "cost"
    direction: MetricDirection = MetricDirection.LOWER_IS_BETTER

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        if not results:
            return MetricResult(
                name=self.name,
                value=0.0,
                formatted_value="$0.0000",
                direction=self.direction.value,
                description="Total monetary cost in USD",
            )

        costs = [r.output.cost for r in results if r.output.cost is not None]
        total_cost = sum(costs) if costs else 0.0
        avg_cost = total_cost / len(results) if results else 0.0

        return MetricResult(
            name=self.name,
            value=total_cost,
            formatted_value=f"${total_cost:.4f}",
            direction=self.direction.value,
            description="Total monetary cost in USD",
            details={
                "total_cost": total_cost,
                "average_cost": avg_cost,
                "reported_runs": len(costs),
            },
        )
