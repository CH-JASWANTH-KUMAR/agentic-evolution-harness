"""Experiment comparison engine computing directional metric deltas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from harness.core.experiment import Experiment


class MetricDelta(BaseModel):
    """Comparative delta for a single metric between two experiment runs."""

    name: str
    v1_value: float
    v2_value: float
    v1_formatted: str
    v2_formatted: str
    delta: float
    pct_delta: float | None = None
    direction: str = "higher_is_better"
    is_improvement: bool = False
    is_regression: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ExperimentComparison(BaseModel):
    """Complete comparative analysis of two experiment runs."""

    baseline_id: str
    candidate_id: str
    baseline_name: str
    candidate_name: str
    deltas: dict[str, MetricDelta] = Field(default_factory=dict)
    common_tests: int = 0
    newly_passed_tests: list[str] = Field(default_factory=list)
    newly_failed_tests: list[str] = Field(default_factory=list)


class ExperimentComparator:
    """Compares baseline vs candidate experiment runs with direction awareness."""

    @classmethod
    def compare(
        cls,
        baseline: Experiment,
        candidate: Experiment,
    ) -> ExperimentComparison:
        deltas: dict[str, MetricDelta] = {}

        # 1. Compare common metrics
        all_metric_names = set(baseline.metrics.keys()).union(candidate.metrics.keys())
        for m_name in sorted(all_metric_names):
            m_v1 = baseline.metrics.get(m_name)
            m_v2 = candidate.metrics.get(m_name)

            if m_v1 is None or m_v2 is None:
                continue

            v1_val = m_v1.value
            v2_val = m_v2.value
            diff = v2_val - v1_val
            pct = (diff / v1_val * 100.0) if v1_val != 0 else None
            direction = m_v2.direction

            if direction == "higher_is_better":
                is_improvement = diff > 1e-6
                is_regression = diff < -1e-6
            elif direction == "lower_is_better":
                is_improvement = diff < -1e-6
                is_regression = diff > 1e-6
            else:
                is_improvement = False
                is_regression = False

            deltas[m_name] = MetricDelta(
                name=m_name,
                v1_value=v1_val,
                v2_value=v2_val,
                v1_formatted=m_v1.formatted_value,
                v2_formatted=m_v2.formatted_value,
                delta=diff,
                pct_delta=pct,
                direction=direction,
                is_improvement=is_improvement,
                is_regression=is_regression,
            )

        # 2. Compare per-test outcomes
        base_test_map = {r.test_case.name: r.passed for r in baseline.results}
        cand_test_map = {r.test_case.name: r.passed for r in candidate.results}

        common_tests = set(base_test_map.keys()).intersection(cand_test_map.keys())
        newly_passed: list[str] = []
        newly_failed: list[str] = []

        for name in common_tests:
            if not base_test_map[name] and cand_test_map[name]:
                newly_passed.append(name)
            elif base_test_map[name] and not cand_test_map[name]:
                newly_failed.append(name)

        return ExperimentComparison(
            baseline_id=baseline.id,
            candidate_id=candidate.id,
            baseline_name=baseline.name,
            candidate_name=candidate.name,
            deltas=deltas,
            common_tests=len(common_tests),
            newly_passed_tests=newly_passed,
            newly_failed_tests=newly_failed,
        )
