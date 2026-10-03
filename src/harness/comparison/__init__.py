"""Comparison and regression detection module for Agentic Evolution Harness."""

from harness.comparison.comparator import (
    ExperimentComparator,
    ExperimentComparison,
    MetricDelta,
)
from harness.comparison.regression import (
    RegressionDetector,
    RegressionReport,
    RegressionViolation,
)

__all__ = [
    "ExperimentComparator",
    "ExperimentComparison",
    "MetricDelta",
    "RegressionDetector",
    "RegressionReport",
    "RegressionViolation",
]
