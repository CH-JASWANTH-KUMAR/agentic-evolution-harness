# Concepts: Evaluators

## What is an Evaluator?

An **Evaluator** is an assertion plugin that inspects a single `(TestCase, AgentOutput)` pair and produces an `EvaluationResult`.

### The Interface

```python
from typing import Protocol, runtime_checkable
from harness.core.agent import AgentOutput
from harness.core.result import EvaluationResult
from harness.core.testcase import TestCase


@runtime_checkable
class Evaluator(Protocol):
    name: str

    def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult: ...
```

### The Output: `EvaluationResult`

Each evaluation result provides:
- `evaluator`: The identifier of the evaluator (e.g., `exact_match`, `contains`).
- `score`: A normalized floating point score between `0.0` and `1.0`.
- `passed`: A boolean flag indicating whether the assertion was met.
- `explanation`: A human-readable description of why the test passed or failed.
- `details`: A dictionary containing debug context (e.g., mismatched keys, diffs).

### Built-in Evaluators

1. **`ExactMatchEvaluator`** (`exact_match`): Strict string equality with optional case and whitespace normalization.
2. **`ContainsEvaluator`** (`contains`): Checks if expected text or regex pattern is present in output.
3. **`JSONMatchEvaluator`** (`json_match`): Structural and semantic JSON equality, with subset verification and list order flexibility.
4. **`ToolUsageEvaluator`** (`tool_usage`): Validates tool call sequences, ordered trajectories, forbidden tools, and argument matches.
