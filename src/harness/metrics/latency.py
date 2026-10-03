"""Latency metric measuring agent execution durations."""

from __future__ import annotations

from collections.abc import Sequence

from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection, MetricRegistry


@MetricRegistry.register("latency")
class LatencyMetric:
    """Calculates average execution latency across all test runs."""

    name: str = "latency"
    direction: MetricDirection = MetricDirection.LOWER_IS_BETTER

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        if not results:
            return MetricResult(
                name=self.name,
                value=0.0,
                formatted_value="0.00s",
                direction=self.direction.value,
                description="Average execution latency in seconds",
            )

        latencies = [
            r.output.latency if r.output.latency is not None else r.duration for r in results
        ]
        avg_latency = sum(latencies) / len(latencies)

        return MetricResult(
            name=self.name,
            value=avg_latency,
            formatted_value=f"{avg_latency:.2f}s",
            direction=self.direction.value,
            description="Average execution latency in seconds",
            details={
                "min": min(latencies),
                "max": max(latencies),
                "avg": avg_latency,
            },
        )
