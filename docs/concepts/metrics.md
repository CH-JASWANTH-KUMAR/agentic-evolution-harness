# Concepts: Metrics

## What is a Metric?

While an **Evaluator** inspects a single test run, a **Metric** aggregates performance across an entire collection of test results in an evaluation run.

### The Interface

```python
from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection


@runtime_checkable
class Metric(Protocol):
    name: str
    direction: MetricDirection

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult: ...
```

### Metric Directionality

Metrics must specify their direction:
- `HIGHER_IS_BETTER`: An increase in value is an improvement (e.g. `success_rate`, `accuracy`, `reliability`).
- `LOWER_IS_BETTER`: A decrease in value is an improvement (e.g. `latency`, `cost`, `error_rate`).
- `NEUTRAL`: Informational metrics without positive/negative optimization direction.

### Built-in Metrics

| Metric Name | Direction | Calculation |
| :--- | :--- | :--- |
| `success_rate` | `HIGHER_IS_BETTER` | `passed_tests / total_tests` |
| `accuracy` | `HIGHER_IS_BETTER` | Mean score across all evaluators |
| `latency` | `LOWER_IS_BETTER` | Mean execution duration in seconds |
| `cost` | `LOWER_IS_BETTER` | Total monetary cost across test runs |
| `reliability` | `HIGHER_IS_BETTER` | Percentage of crash-free executions |
