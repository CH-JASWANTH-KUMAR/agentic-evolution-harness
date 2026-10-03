# Architecture Specification

## Overview

The **Agentic Evolution Harness** is built around three core architectural tenets:
1. **Framework Agnosticism**: No hard-coded reliance on LangChain, AutoGen, CrewAI, or any single model provider.
2. **Protocol-Driven Extensibility**: Extensibility points (`Agent`, `Evaluator`, `Metric`, `Reporter`) are defined as Python Protocols (`PEP 544`), avoiding rigid inheritance trees.
3. **Deterministic Evaluation Pipeline**: Built-in evaluators run locally without external API calls or network flakiness.

---

## System Layers

```text
┌────────────────────────────────────────────────────────┐
│                        CLI                             │
│       harness evaluate / compare / validate            │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │ Benchmark Loader │        │   Agent Runner   │
    └─────────┬────────┘        └─────────┬────────┘
              │                           │
              │         ┌─────────────────┼─────────────────┐
              │         ▼                 ▼                 ▼
              │   ┌───────────┐     ┌───────────┐     ┌───────────┐
              └──►│Evaluators │     │  Metrics  │     │ Adapters  │
                  └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
                        │                 │                 │
                        └─────────┬───────┴─────────────────┘
                                  ▼
                        ┌───────────────────┐
                        │    Core Domain    │
                        │ (TestCase/Result) │
                        └───────────────────┘
```

### 1. Core Domain (`harness.core`)
The immutable foundation. It defines value objects:
- `TestCase`: An isolated test case with input, expected output, tags, and evaluator configurations.
- `AgentOutput`: The standardized return type of any agent under test (output, latency, token usage, cost, tool calls, error).
- `Trace` & `ToolCallRecord`: Records of observable agent actions and tool invocations.
- `EvaluationResult`: The output of a single evaluator verifying a single test case.
- `TestCaseResult`: The outcome of all evaluators for one test case.
- `Experiment`: The complete evaluation artifact, including metadata, test results, and aggregated metrics.

### 2. Evaluators (`harness.evaluators`)
Evaluators answer: **"Did this individual test case pass?"**
Each evaluator implements the `Evaluator` protocol:
```python
def evaluate(self, test_case: TestCase, output: AgentOutput) -> EvaluationResult: ...
```
Evaluators are decoupled and discovered through `EvaluatorRegistry`.

### 3. Metrics (`harness.metrics`)
Metrics answer: **"How did the agent perform across the entire test suite?"**
Each metric implements the `Metric` protocol and explicitly specifies its `MetricDirection`:
```python
class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"
```
This enables automated, directional delta analysis between different agent runs.

### 4. Adapters (`harness.adapters`)
Any agent can be plugged into the harness:
- `GenericAgent`: Wraps any Python function or class callable.
- `MockAgent`: Deterministic mock agent with response mappings and simulated latencies.
- `SubprocessAgent`: Runs external CLI processes.

### 5. Runner (`harness.runner`)
The `AgentRunner` orchestrates the pipeline:
1. Runs each test case against the agent.
2. Measures execution duration.
3. Invokes assigned evaluators.
4. Aggregates test outcomes.
5. Computes all configured metrics.
6. Packages the result into an `Experiment` model.

### 6. Comparison & Regression (`harness.comparison`)
Enables iterative agent evolution:
- `ExperimentComparator`: Computes metric deltas and detects which tests regressed or improved.
- `RegressionDetector`: Enforces performance thresholds (e.g. minimum success rate or maximum latency) and fails CI if violated.
