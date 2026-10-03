"""Regression detector enforcing performance thresholds and CI pass/fail gates."""

from __future__ import annotations

from pydantic import BaseModel, Field

from harness.core.experiment import Experiment


class RegressionViolation(BaseModel):
    """Details of a failed regression threshold check."""

    metric_name: str
    condition: str
    threshold_value: float
    actual_value: float
    message: str


class RegressionReport(BaseModel):
    """Summary of regression evaluation across an experiment."""

    passed: bool
    violations: list[RegressionViolation] = Field(default_factory=list)
    checked_metrics: int = 0


class RegressionDetector:
    """Evaluates an experiment against absolute or relative regression thresholds."""

    @classmethod
    def check_thresholds(
        cls,
        experiment: Experiment,
        thresholds: dict[str, dict[str, float]],
    ) -> RegressionReport:
        violations: list[RegressionViolation] = []
        checked = 0

        for metric_name, rules in thresholds.items():
            if metric_name not in experiment.metrics:
                continue

            checked += 1
            actual = experiment.metrics[metric_name].value

            # Check minimum bound (e.g. success_rate >= 0.80)
            if "minimum" in rules or "min" in rules:
                min_val = rules.get("minimum", rules.get("min", 0.0))
                if actual < min_val:
                    violations.append(
                        RegressionViolation(
                            metric_name=metric_name,
                            condition="minimum",
                            threshold_value=min_val,
                            actual_value=actual,
                            message=f"{metric_name} was {actual:.4f}, below required minimum of {min_val:.4f}",
                        )
                    )

            # Check maximum bound (e.g. latency <= 2.0s)
            if "maximum" in rules or "max" in rules:
                max_val = rules.get("maximum", rules.get("max", float("inf")))
                if actual > max_val:
                    violations.append(
                        RegressionViolation(
                            metric_name=metric_name,
                            condition="maximum",
                            threshold_value=max_val,
                            actual_value=actual,
                            message=f"{metric_name} was {actual:.4f}, exceeding maximum allowed {max_val:.4f}",
                        )
                    )

        return RegressionReport(
            passed=len(violations) == 0,
            violations=violations,
            checked_metrics=checked,
        )
