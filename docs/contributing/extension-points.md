# Contributor Extensibility Guide

This document is the definitive guide to the **stable extension points** of the Agentic Evolution Harness for Hacktoberfest and open-source contributors.

The framework is architected using **structural subtyping (`typing.Protocol`)** and **decoupled registries**. This ensures external contributors can implement a new evaluator, metric, adapter, reporter, or benchmark dataset in an isolated file without modifying runner orchestration, core data models, or unrelated modules.

---

## Architectural Boundaries: What Contributors Should Generally NOT Modify

To ensure modularity and avoid breaking core invariants, the codebase maintains strict separation between **Core Foundation** (stable) and **Extension Plugins** (open for contribution).

### Core Modules Contributors Should Generally NOT Modify

Contributors should **NOT** modify the following modules unless an assigned GitHub issue explicitly requires an architectural refactor:

1. **Core Models (`src/harness/core/`)**:
   - `testcase.py`: Data structure defining test cases (`TestCase`).
   - `agent.py`: Output and trajectory data structures (`AgentOutput`, `ToolCallRecord`, `Trace`).
   - `result.py`: Execution and evaluation models (`EvaluationResult`, `TestCaseResult`).
   - `experiment.py`: Central lifecycle and storage container (`Experiment`, `MetricResult`, `ExperimentState`).
2. **Runner Orchestration (`src/harness/runner/`)**:
   - `runner.py`: Execution pipeline, timing, timeout enforcement, and dependency coordination (`AgentRunner`).
3. **Experiment Lifecycle**:
   - The sequential phases of experiment execution: Setup → Agent Invocation → Per-test Evaluation → Aggregate Metrics Calculation → Result Assembly.
4. **Configuration Architecture (`src/harness/benchmarks/schema.py`, `loader.py`)**:
   - The central Pydantic schema validation for benchmarks.

### Stable Extension Zones (Where Contributions Belong)

Contributors can implement new features completely within these isolated areas:

```text
ALLOWED EXTENSION POINTS:
├── src/harness/evaluators/       # Add single-test evaluation plugins
├── src/harness/metrics/          # Add aggregate metric plugins
├── src/harness/adapters/         # Add agent framework connectors (HTTP, MCP, CLI)
├── src/harness/reporters/        # Add output generators (CSV, HTML, JUnit XML)
├── src/harness/comparison/       # Add statistical comparators & regression checkers
├── src/harness/cli/              # Add CLI subcommands
└── benchmarks/examples/          # Add declarative benchmark datasets (YAML/JSON)
```

---

## 1. Creating an Evaluator

Evaluators answer: **"Did the agent pass or fail this specific test case, and what is its score?"**

### Location
- **Implementation**: `src/harness/evaluators/<evaluator_name>.py`
- **Registration export**: `src/harness/evaluators/__init__.py`
- **Unit tests**: `tests/unit/evaluators/test_<evaluator_name>.py`

### Interface
From `src/harness/evaluators/base.py`:

```python
from typing import Protocol, runtime_checkable
from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase


@runtime_checkable
class Evaluator(Protocol):
    name: str

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        """Evaluate agent output against expected result in a test case."""
        ...
```

### Registration
Use the `@EvaluatorRegistry.register("<name>")` decorator:

```python
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("fuzzy_match")
class FuzzyMatchEvaluator:
    name: str = "fuzzy_match"
    ...
```

### Required Behavior
- **Normalized Score**: Must return `score: float` strictly between `0.0` and `1.0`.
- **Pass/Fail Decision**: Must return `passed: bool`.
- **Explanatory Message**: Must return a helpful `explanation: str` detailing the rationale for the score.
- **Error Handling**: Must inspect `output.is_error`. If true, return `EvaluationResult(score=0.0, passed=False, explanation=...)` without throwing an unhandled exception.
- **Configurable Options**: Any configuration (e.g. `threshold: float = 0.8`) must be initialized via `__init__`.

### Minimal Working Example

```python
# src/harness/evaluators/fuzzy_match.py
from __future__ import annotations

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("fuzzy_match")
class FuzzyMatchEvaluator:
    """Evaluates text similarity based on character set overlap."""

    name: str = "fuzzy_match"

    def __init__(self, threshold: float = 0.8) -> None:
        self.threshold = threshold

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        if output.is_error:
            return EvaluationResult(
                evaluator=self.name,
                score=0.0,
                passed=False,
                explanation=f"Agent produced an error: {output.error}",
            )

        expected = str(test_case.expected or "").lower()
        actual = output.text.lower()

        if not expected:
            return EvaluationResult(
                evaluator=self.name,
                score=1.0,
                passed=True,
                explanation="No expected output specified; passed by default.",
            )

        set_expected = set(expected)
        set_actual = set(actual)
        overlap = len(set_expected & set_actual) / len(set_expected) if set_expected else 1.0
        passed = overlap >= self.threshold

        return EvaluationResult(
            evaluator=self.name,
            score=round(overlap, 4),
            passed=passed,
            explanation=f"Character overlap was {overlap:.2f} (threshold: {self.threshold:.2f}).",
            details={"actual": actual, "expected": expected, "overlap": overlap},
        )
```

### Required Tests
In `tests/unit/evaluators/test_fuzzy_match.py`:
- Test passing score when similarity exceeds threshold.
- Test failing score when similarity falls below threshold.
- Test error isolation when `output.is_error == True`.
- Test handling of edge cases (empty strings, missing expected value).

### Core Parts NOT to Modify
- Do not modify `TestCase`, `AgentOutput`, `EvaluationResult`, or `AgentRunner`.

---

## 2. Creating a Metric

Metrics answer: **"How did the agent perform across the entire suite of test results?"**

### Location
- **Implementation**: `src/harness/metrics/<metric_name>.py`
- **Registration export**: `src/harness/metrics/__init__.py`
- **Unit tests**: `tests/unit/metrics/test_<metric_name>.py`

### Interface
From `src/harness/metrics/base.py`:

```python
from collections.abc import Sequence
from enum import StrEnum
from typing import Protocol, runtime_checkable
from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult


class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"


@runtime_checkable
class Metric(Protocol):
    name: str
    direction: MetricDirection

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        """Compute aggregate metric across all test case results."""
        ...
```

### Registration
Use the `@MetricRegistry.register("<name>")` decorator:

```python
from harness.metrics.base import MetricRegistry


@MetricRegistry.register("p95_latency")
class P95LatencyMetric:
    name: str = "p95_latency"
    ...
```

### Required Behavior
- **Directionality**: Must set `direction` to `MetricDirection.HIGHER_IS_BETTER`, `LOWER_IS_BETTER`, or `NEUTRAL`.
- **Zero-Division Safety**: Must handle empty result sequences (`len(results) == 0`) cleanly.
- **Formatted Value**: Must provide a readable `formatted_value: str` (e.g. `"1.25s"`, `"95.0%"`).

### Minimal Working Example

```python
# src/harness/metrics/p95_latency.py
from __future__ import annotations

from collections.abc import Sequence

from harness.core.experiment import MetricResult
from harness.core.result import TestCaseResult
from harness.metrics.base import MetricDirection, MetricRegistry


@MetricRegistry.register("p95_latency")
class P95LatencyMetric:
    """Calculates 95th percentile execution latency across test cases."""

    name: str = "p95_latency"
    direction: MetricDirection = MetricDirection.LOWER_IS_BETTER

    def calculate(self, results: Sequence[TestCaseResult]) -> MetricResult:
        if not results:
            return MetricResult(
                name=self.name,
                value=0.0,
                formatted_value="0.00s",
                direction=self.direction.value,
                description="95th percentile execution latency",
            )

        latencies = sorted(
            r.output.latency if r.output.latency is not None else r.duration for r in results
        )
        idx = int(0.95 * len(latencies))
        p95_val = latencies[min(idx, len(latencies) - 1)]

        return MetricResult(
            name=self.name,
            value=p95_val,
            formatted_value=f"{p95_val:.2f}s",
            direction=self.direction.value,
            description="95th percentile execution latency in seconds",
            details={"sample_size": len(results), "p95": p95_val},
        )
```

### Required Tests
In `tests/unit/metrics/test_p95_latency.py`:
- Test calculation with multiple latency values.
- Test fallback when `output.latency` is `None` (uses `r.duration`).
- Test empty list edge case (`results = []`).
- Verify correct `MetricDirection`.

### Core Parts NOT to Modify
- Do not modify `MetricResult`, `TestCaseResult`, or `Experiment`.

---

## 3. Creating an Agent Adapter

Adapters bridge third-party agent interfaces, REST services, or CLI processes into the standard `Agent` protocol.

### Location
- **Implementation**: `src/harness/adapters/<adapter_name>.py`
- **Registration export**: `src/harness/adapters/__init__.py`
- **Unit tests**: `tests/unit/adapters/test_<adapter_name>.py`

### Interface
From `src/harness/core/agent.py` and `src/harness/adapters/base.py`:

```python
from typing import Any, Protocol, runtime_checkable
from harness.core.agent import AgentOutput


@runtime_checkable
class Agent(Protocol):
    def run(
        self,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AgentOutput: ...


@runtime_checkable
class AgentAdapter(Protocol):
    def create_agent(self, **config: Any) -> Agent: ...
```

### Registration
Use the `@AdapterRegistry.register("<name>")` decorator:

```python
from harness.adapters.base import AdapterRegistry


@AdapterRegistry.register("echo")
class EchoAgent: ...
```

### Required Behavior
- **Output Return**: Must return an `AgentOutput` model containing `output` (str or dict), `latency` (seconds), and optional `tool_calls` and `metadata`.
- **Exception Containment**: Must catch internal agent/network exceptions and return `AgentOutput(output="", error=str(e))` rather than crashing the harness.

### Minimal Working Example

```python
# src/harness/adapters/echo.py
from __future__ import annotations

import time
from typing import Any

from harness.adapters.base import AdapterRegistry
from harness.core.agent import AgentOutput


@AdapterRegistry.register("echo")
class EchoAgent:
    """Minimal adapter echoing input with prefix."""

    def __init__(self, prefix: str = "Echo: ") -> None:
        self.prefix = prefix

    def run(
        self,
        input: str | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> AgentOutput:
        start = time.perf_counter()
        try:
            text_input = input if isinstance(input, str) else str(input)
            result = f"{self.prefix}{text_input}"
            return AgentOutput(
                output=result,
                latency=time.perf_counter() - start,
                metadata={"adapter": "echo"},
            )
        except Exception as exc:
            return AgentOutput(
                output="",
                error=str(exc),
                latency=time.perf_counter() - start,
            )
```

### Required Tests
In `tests/unit/adapters/test_echo.py`:
- Test successful text response and latency reporting.
- Test handling of dictionary input.
- Test error isolation when an exception is simulated.

### Core Parts NOT to Modify
- Do not modify `AgentOutput` or `AgentRunner`.

---

## 4. Creating a Reporter

Reporters serialize completed `Experiment` results into various formats (CSV, HTML, JUnit XML, Markdown).

### Location
- **Implementation**: `src/harness/reporters/<format_name>.py`
- **Registration export**: `src/harness/reporters/__init__.py`
- **Unit tests**: `tests/unit/reporters/test_<format_name>.py`

### Interface
From `src/harness/reporters/base.py`:

```python
from pathlib import Path
from typing import Protocol, runtime_checkable
from harness.core.experiment import Experiment


@runtime_checkable
class Reporter(Protocol):
    def report(self, experiment: Experiment, destination: Path | None = None) -> str:
        """Generate formatted report string, writing to destination if provided."""
        ...
```

### Registration
Use the `@ReporterRegistry.register("<name>")` decorator:

```python
from harness.reporters.base import ReporterRegistry


@ReporterRegistry.register("csv")
class CSVReporter: ...
```

### Required Behavior
- **Return Value**: Must always return the generated report as a `str`.
- **Destination Support**: If `destination: Path` is provided, create parent directories (`destination.parent.mkdir(parents=True, exist_ok=True)`) and write the content to disk.

### Minimal Working Example

```python
# src/harness/reporters/csv.py
from __future__ import annotations

import csv
import io
from pathlib import Path

from harness.core.experiment import Experiment
from harness.reporters.base import ReporterRegistry


@ReporterRegistry.register("csv")
class CSVReporter:
    """Exports test case results into a CSV format."""

    def report(self, experiment: Experiment, destination: Path | None = None) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["test_id", "status", "duration_seconds", "evaluator_scores"])

        for result in experiment.results:
            scores = "; ".join(f"{e.evaluator}:{e.score:.2f}" for e in result.evaluations)
            writer.writerow([result.test_id, result.status.value, f"{result.duration:.4f}", scores])

        content = output.getvalue()
        if destination is not None:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

        return content
```

### Required Tests
In `tests/unit/reporters/test_csv.py`:
- Test generating CSV string from mock `Experiment`.
- Test saving to disk when `destination` is provided.
- Verify headers and column formatting.

### Core Parts NOT to Modify
- Do not modify `Experiment`, `TestCaseResult`, or `MetricResult`.

---

## 5. Adding a Benchmark Dataset

Benchmarks are declarative test suites defined in YAML or JSON. Adding a benchmark requires **zero changes to Python code**.

### Location
- **Directory**: `benchmarks/examples/<benchmark_name>.yaml`

### Interface / Schema
Conforms to `BenchmarkConfig` in `src/harness/benchmarks/schema.py`:

```yaml
version: "1.0"
name: "customer-support-eval"
description: "Evaluates support intent classification and tool execution."

agent:
  adapter: generic
  module: "examples.basic.mock_agent:support_agent"

evaluators:
  - name: exact_match

metrics:
  - success_rate
  - accuracy
  - latency

thresholds:
  success_rate:
    minimum: 0.80

tests:
  - id: "refund-001"
    name: "refund_intent"
    input: "My item was damaged during delivery. Please refund my order."
    expected: "Refund of $49.99 processed"
    evaluators:
      - name: contains
        options:
          substring: "Refund of $49.99 processed"
    tags: ["billing", "refunds"]
```

### Registration & Discovery
- Benchmark files are discovered automatically by path when running:
  ```bash
  uv run harness run benchmarks/examples/<benchmark_name>.yaml
  ```

### Required Behavior
- Must include `version: "1.0"`, unique `name`, valid `agent` configuration, and at least one test case in `tests`.
- Each test must have an `id`, `input`, and optional `expected` output.

### Validation & Testing
Contributors validate benchmarks without running an agent:

```bash
uv run harness validate benchmarks/examples/<benchmark_name>.yaml
```

### Core Parts NOT to Modify
- Do not modify `src/harness/benchmarks/schema.py` or `loader.py`.

---

## 6. CLI Extensions

The CLI is built with **Typer** and formatted with **Rich**.

### Location
- **Command implementation**: `src/harness/cli/<subcommand>.py`
- **Registration**: `src/harness/cli/main.py`
- **Integration tests**: `tests/integration/test_cli.py`

### Interface
Standard Typer command functions with type annotations and docstrings:

```python
import typer


def run_mycommand(
    arg: str = typer.Argument(..., help="Positional argument."),
    option: bool = typer.Option(False, "--flag", help="Optional flag."),
) -> None:
    """Command description for CLI help output."""
    ...
```

### Registration
Register on the Typer `app` in `src/harness/cli/main.py`:

```python
from harness.cli.mycommand import run_mycommand

app.command(name="mycommand")(run_mycommand)
```

### Required Behavior
- Output rich, user-friendly tables and panels using `rich.console.Console`.
- Exit with code `0` on success and non-zero (via `raise typer.Exit(code=1)`) on error.

### Minimal Working Example

```python
# src/harness/cli/export.py
from __future__ import annotations

from pathlib import Path
import typer
from rich.console import Console

console = Console()


def run_export(
    input_file: Path = typer.Argument(..., help="Path to experiment JSON file."),
    format: str = typer.Option("csv", "--format", "-f", help="Export target format."),
) -> None:
    """Export an experiment JSON artifact to another format."""
    if not input_file.exists():
        console.print(f"[bold red]Error:[/] File {input_file} not found.")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Exporting[/] {input_file} to {format} format...")
```

### Required Tests
In `tests/integration/test_cli.py` using `CliRunner`:
- Test command invocation with valid arguments.
- Test error handling when file is not found.

### Core Parts NOT to Modify
- Do not modify existing options or signatures of `harness run`, `harness compare`, or `harness validate`.

---

## 7. Model Context Protocol (MCP) Integrations

The harness supports evaluating agents that produce structured tool call traces conforming to the Model Context Protocol (MCP).

### Location
- **MCP Evaluators**: `src/harness/evaluators/mcp_<name>.py`
- **MCP Adapters**: `src/harness/adapters/mcp_<name>.py`
- **Tests**: `tests/unit/evaluators/test_mcp_<name>.py`

### Interfaces & Data Structures
From `src/harness/core/agent.py`:

```python
class ToolCallRecord(BaseModel):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    duration: float | None = None
    status: str = "success"  # "success" or "error"


class Trace(BaseModel):
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
```

### Required Behavior
- Evaluators inspect `output.tool_calls` or `output.trace.tool_calls`.
- Validate that required MCP tools were invoked, tool parameters were correctly formatted, and execution order was respected.

### Minimal Working Example

```python
# src/harness/evaluators/mcp_tool_usage.py
from __future__ import annotations

from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase
from harness.evaluators.base import EvaluatorRegistry


@EvaluatorRegistry.register("mcp_tool_usage")
class MCPToolUsageEvaluator:
    """Verifies that the agent invoked expected MCP tools."""

    name: str = "mcp_tool_usage"

    def __init__(self, required_tool: str = "database_query") -> None:
        self.required_tool = required_tool

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult:
        invoked_tools = [call.tool_name for call in output.tool_calls]
        passed = self.required_tool in invoked_tools

        return EvaluationResult(
            evaluator=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            explanation=f"Required tool '{self.required_tool}' was {'invoked' if passed else 'missing'}.",
            details={"invoked_tools": invoked_tools},
        )
```

### Required Tests
- Test passing case where required tool is present in `output.tool_calls`.
- Test failing case where required tool is absent.

### Core Parts NOT to Modify
- Do not modify `ToolCallRecord` or `Trace` core schema models.

---

## 8. Comparison & Regression Functionality

The comparison module detects performance shifts, improvements, and regressions between two experiment runs.

### Location
- **Implementation**: `src/harness/comparison/`
- **Unit tests**: `tests/unit/comparison/test_comparator.py`, `test_regression.py`

### Interfaces & Data Structures
From `src/harness/comparison/comparator.py` and `regression.py`:

```python
class MetricDelta(BaseModel):
    name: str
    v1_value: float
    v2_value: float
    delta: float
    is_improvement: bool
    is_regression: bool


class RegressionViolation(BaseModel):
    metric_name: str
    condition: str
    threshold_value: float
    actual_value: float
    message: str
```

### Required Behavior
- Direction-aware delta calculations (respecting `higher_is_better` vs `lower_is_better`).
- Safe handling of zero division when calculating percentage differences.
- Accurate reporting of metric violations against threshold rules.

### Minimal Working Example

```python
from harness.comparison.comparator import ExperimentComparator
from harness.comparison.regression import RegressionDetector

# 1. Compare baseline vs candidate runs
comparison = ExperimentComparator.compare(baseline_experiment, candidate_experiment)

# 2. Check regression rules
report = RegressionDetector.check_thresholds(
    candidate_experiment,
    thresholds={"success_rate": {"minimum": 0.85}},
)
```

### Required Tests
- Test delta calculations for metrics with `higher_is_better` and `lower_is_better`.
- Test regression violation detection when a metric falls below minimum threshold.

### Core Parts NOT to Modify
- Do not modify `ExperimentComparison` or `RegressionViolation` core fields.

---

## Verification Checklist for Contributors

Before opening a pull request, run the complete verification suite locally:

```bash
# 1. Run all unit and integration tests
uv run pytest

# 2. Check code style and formatting
uv run ruff check .
uv run ruff format --check .

# 3. Verify strict type checking
uv run mypy src

# Or run all quality checks at once:
make check
```
