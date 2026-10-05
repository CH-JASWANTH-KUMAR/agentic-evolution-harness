# Contributing to Agentic Evolution Harness 🧬

Welcome! Whether you are participating in **Hacktoberfest**, adding your first open-source pull request, or designing advanced agent benchmarking algorithms, we are thrilled to have you here.

This document is your complete roadmap for contributing.

> 💡 **Looking for complete protocol specifications and working examples?**
> Read the [Contributor Extensibility Guide](docs/contributing/extension-points.md) for detailed interface contracts, registration mechanisms, required tests, and architectural boundaries.

---

## 🧭 Where Should I Contribute?

Use this decision table to find exactly which directory and test suite your contribution belongs to:

| I want to... | Target Implementation Directory | Matching Unit Test Directory | Difficulty |
| :--- | :--- | :--- | :--- |
| **Add a new Evaluator** | `src/harness/evaluators/` | `tests/unit/evaluators/` | 🟢 Beginner / 🟡 Intermediate |
| **Add a new Metric** | `src/harness/metrics/` | `tests/unit/metrics/` | 🟢 Beginner |
| **Add an Agent Adapter** | `src/harness/adapters/` | `tests/unit/adapters/` | 🟡 Intermediate |
| **Add a Reporter** | `src/harness/reporters/` | `tests/unit/reporters/` | 🟡 Intermediate |
| **Add a Benchmark Dataset** | `benchmarks/examples/` | `tests/integration/` | 🟢 Beginner |
| **Improve the CLI** | `src/harness/cli/` | `tests/integration/test_cli.py` | 🟡 Intermediate |
| **Implement LLM-as-a-Judge** | `src/harness/evaluators/` | `tests/unit/evaluators/` | 🔴 Advanced |
| **Add Regression / Stats Tools** | `src/harness/comparison/` | `tests/unit/comparison/` | 🔴 Advanced |
| **Improve Documentation** | `docs/` or `README.md` | *None* | 🟢 Beginner |

---

## ⚡ 5-Minute Local Setup

We recommend [`uv`](https://github.com/astral-sh/uv) for fast, reproducible Python dependency management, but standard `pip` in a virtual environment works too.

### 1. Fork & Clone

```bash
git clone https://github.com/<your-username>/harness.git
cd harness
```

### 2. Install Dependencies

Using `uv`:
```bash
uv sync --all-extras
```

Or using standard `pip`:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Verify Setup

Run the test suite and linters to verify everything is green:

```bash
# Run pytest with coverage
uv run pytest

# Check code formatting and linting
uv run ruff check .
uv run ruff format --check .

# Run type checker
uv run mypy src
```

Or simply run:
```bash
make check
```

---

## 🛠️ Step-by-Step Guides

### Guide 1: How to Add a New Evaluator

Evaluators assess a single test case execution.

1. **Create your evaluator file** in `src/harness/evaluators/<name>.py`:

```python
from __future__ import annotations

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("fuzzy_match")
class FuzzyMatchEvaluator:
    """Evaluates whether agent output matches expected text above a similarity threshold."""

    name: str = "fuzzy_match"

    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        if output.is_error:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Agent error: {output.error}",
            )

        # Your evaluation logic here...
        score = 1.0  # Normalized float between 0.0 and 1.0
        passed = score >= self.threshold

        return EvaluationResult(
            evaluator=self.name,
            score=score,
            passed=passed,
            explanation=f"Fuzzy similarity score {score:.2f} (threshold: {self.threshold:.2f}).",
        )
```

2. **Register it in `src/harness/evaluators/__init__.py`**:
   Import your class and add it to `__all__`.

3. **Add unit tests** in `tests/unit/evaluators/test_<name>.py`:
   Test positive matches, negative mismatches, and edge cases.

4. **Verify**:
   ```bash
   uv run harness list-plugins evaluators
   uv run pytest tests/unit/evaluators/test_<name>.py
   ```

---

### Guide 2: How to Add a New Metric

Metrics aggregate performance across all executed test cases in an experiment.

1. **Create your metric file** in `src/harness/metrics/<name>.py`:

```python
from __future__ import annotations

from collections.abc import Sequence
from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection, MetricRegistry


@MetricRegistry.register("p95_latency")
class P95LatencyMetric:
    """Calculates 95th percentile execution latency across test cases."""

    name: str = "p95_latency"
    # Specify whether higher or lower numbers represent an improvement!
    direction: MetricDirection = MetricDirection.LOWER_IS_BETTER

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        if not results:
            return MetricResult(
                name=self.name,
                value=0.0,
                formatted_value="0.00s",
                direction=self.direction.value,
                description="95th percentile latency",
            )

        latencies = sorted(r.duration for r in results)
        idx = int(0.95 * len(latencies))
        p95 = latencies[min(idx, len(latencies) - 1)]

        return MetricResult(
            name=self.name,
            value=p95,
            formatted_value=f"{p95:.2f}s",
            direction=self.direction.value,
            description="95th percentile execution latency in seconds",
        )
```

2. **Register it in `src/harness/metrics/__init__.py`**.
3. **Add unit tests** in `tests/unit/metrics/test_<name>.py`.

---

### Guide 3: How to Add a Benchmark Dataset

Benchmarks are declarative YAML files that test agent capabilities:

1. **Create a file in `benchmarks/examples/<name>.yaml`**:

```yaml
version: "1.0"
name: "customer-support-triage"
description: "Evaluates multi-intent support routing and refund decisions."

evaluators:
  - name: exact_match

metrics:
  - success_rate
  - accuracy
  - latency

thresholds:
  success_rate:
    minimum: 0.85

tests:
  - id: "triage-001"
    name: "refund_intent"
    input: "I was billed twice for invoice #4412. Please refund the duplicate."
    expected: "Refund requested for invoice #4412."
    evaluators:
      - name: contains
        options:
          substring: "Refund requested"
    tags:
      - billing
      - triage
```

2. **Validate your benchmark using the CLI**:
   ```bash
   uv run harness validate benchmarks/examples/<name>.yaml
   ```

---

## 📋 Pull Request Checklist

Before opening a pull request, ensure:
- [ ] Your code passes all tests: `uv run pytest`
- [ ] Your code is formatted: `uv run ruff format .`
- [ ] No lint errors: `uv run ruff check .`
- [ ] Type checks pass: `uv run mypy src`
- [ ] You have added unit tests covering your changes.
- [ ] You have updated or added documentation where relevant.

Thank you for contributing to the Agentic Evolution Harness!
