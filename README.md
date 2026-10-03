# Agentic Evolution Harness 🧬

[![CI](https://github.com/agentic-evolution/harness/actions/workflows/ci.yml/badge.svg)](https://github.com/agentic-evolution/harness/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)
[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2026-orange.svg)](https://hacktoberfest.com/)

> **A modular, framework-agnostic evaluation and benchmarking harness for AI agents.**

---

## ⚡ What is this?

**Agentic Evolution Harness** is an open-source framework designed to test, benchmark, and iteratively improve AI agents. It decouples agent execution from assertion logic and metric tracking, allowing developers and researchers to systematically measure agent capabilities, detect regressions in CI, and evolve agent performance over time without vendor lock-in.

## 🎯 Why does it exist?

Testing AI agents is fundamentally different from traditional unit testing:
* **Non-deterministic outputs**: Exact string matches often fail even when the agent solved the problem correctly.
* **Complex multi-step trajectories**: Agents call tools, browse, plan, and retry. Evaluating only the final answer ignores reasoning path quality, unnecessary tool calls, and high token costs.
* **Framework lock-in**: Existing evaluation tools often force you to use a specific agent framework (LangChain, AutoGen, CrewAI) or a specific cloud provider.
* **Steep contributor barrier**: Most evaluation repos are monolithic and impenetrable for Hacktoberfest contributors wanting to add simple evaluators or metrics.

The **Agentic Evolution Harness** solves this with a clean, protocol-driven architecture: anyone can add an evaluator or metric in under 30 lines of Python without modifying the core runner.

## 🔄 How does it work?

```
┌─────────────┐     ┌───────────┐     ┌───────────────┐     ┌──────────────────┐
│ DEFINE TEST │ ──► │ RUN AGENT │ ──► │ COLLECT TRACE │ ──► │ EVALUATE RESULTS │
└─────────────┘     └───────────┘     └───────────────┘     └──────────────────┘
                                                                      │
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   │
│  IMPROVE AGENT  │ ◄── │  COMPARE RUNS   │ ◄── │ GENERATE REPORT │ ◄─┘
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Define Test**: Author simple YAML test cases specifying inputs, expected behaviors, and tool expectations.
2. **Run Agent**: Run your agent via a lightweight adapter (generic function, REST API, subprocess, or mock).
3. **Collect Trace**: Capture inputs, outputs, tool invocations, duration, and token usage without recording private internal chains.
4. **Evaluate Results**: Run modular evaluators (`ExactMatch`, `Contains`, `JSONMatch`, `ToolUsage`, or custom plugins).
5. **Calculate Metrics**: Compute aggregate statistics (`Success Rate`, `Accuracy`, `Latency`, `Cost`, `Reliability`).
6. **Generate Report**: View beautiful Rich terminal cards, export JSON artifacts, or generate GitHub Markdown for CI.
7. **Compare Runs**: Compare `v1.json` vs `v2.json` to immediately detect regressions or validate improvements.

---

## 🚀 5-Minute Quick Start

### 1. Installation

Clone the repository and install dependencies using `uv` (recommended) or `pip`:

```bash
git clone https://github.com/agentic-evolution/harness.git
cd harness

# Using uv
uv sync

# Or using pip in a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Run Tests

Verify your setup:

```bash
uv run pytest
```

### 3. Run Your First Benchmark

Evaluate our basic sample agent against a test benchmark:

```bash
uv run harness evaluate examples/basic/benchmark.yaml
```

You'll see a terminal report:

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                   Agentic Evolution Harness                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Benchmark: basic-support-eval
Tests:     5

 ✓  refund_request            [100% | 0.32s]
 ✓  order_status              [100% | 0.18s]
 ✓  weather_lookup            [100% | 0.25s]
 ✗  unknown_intent            [0%   | 0.12s]
 ✓  greeting                  [100% | 0.09s]

Summary Metrics:
────────────────────────────────────────────────────────────
 Success Rate     : 80.0%
 Mean Score       : 0.85
 Average Latency  : 0.19s
 Reliability      : 100.0%

Report saved to: results/latest.json
```

### 4. Compare Agent Iterations

Track evolution between two model versions or prompt revisions:

```bash
uv run harness compare results/v1.json results/v2.json
```

```text
┌───────────────────┬─────────┬─────────┬──────────┐
│ Metric            │ v1      │ v2      │ Delta    │
├───────────────────┼─────────┼─────────┼──────────┤
│ Success Rate      │ 75.0%   │ 90.0%   │ +15.0% ▲ │
│ Average Latency   │ 1.82s   │ 1.25s   │ -0.57s ▼ │
│ Reliability       │ 95.0%   │ 100.0%  │ +5.0%  ▲ │
└───────────────────┴─────────┴─────────┴──────────┘
```

---

## 🧭 Architecture at a Glance

The codebase follows strict separation of concerns:

| Directory | Responsibility | Can I extend it? |
| :--- | :--- | :--- |
| `src/harness/core/` | Core protocols (`Agent`, `Evaluator`, `Metric`) and immutable models (`TestCase`, `AgentOutput`). | Stable core (discuss via RFC) |
| `src/harness/evaluators/` | Individual test evaluators (`ExactMatch`, `Contains`, `JSONMatch`, `ToolUsage`). | **Yes! Easy to add plugins** |
| `src/harness/metrics/` | Aggregate metrics (`SuccessRate`, `Accuracy`, `Latency`, `Cost`). | **Yes! Easy to add plugins** |
| `src/harness/adapters/` | Agent connectors (`generic`, `mock`, `subprocess`, `http`). | **Yes! Add custom adapters** |
| `src/harness/reporters/` | Output formatters (`console`, `json`, `markdown`). | **Yes! Add new reporters** |
| `src/harness/comparison/` | Delta analysis & regression detection. | Extensible comparison math |
| `src/harness/cli/` | Command-line interface powered by Typer and Rich. | Typer subcommands |

---

## 🎃 Hacktoberfest: Where Should I Contribute?

We welcome contributors of all experience levels! See our [Contributing Guide](CONTRIBUTING.md) for step-by-step instructions.

### Quick Decision Tree:

* **I want to add a new evaluator (e.g. Regex, Fuzzy Match, JSONPath)**:
  👉 Go to `src/harness/evaluators/` and follow [Creating an Evaluator](docs/guides/create-evaluator.md).
* **I want to add a new metric (e.g. P95 latency, Token Throughput)**:
  👉 Go to `src/harness/metrics/` and follow [Creating a Metric](docs/guides/create-metric.md).
* **I want to connect a new agent framework**:
  👉 Go to `src/harness/adapters/` and follow [Creating an Adapter](docs/guides/create-agent-adapter.md).
* **I want to contribute benchmark datasets**:
  👉 Go to `benchmarks/examples/` and follow [Adding a Benchmark](docs/guides/add-benchmark.md).
* **I want to improve documentation or tests**:
  👉 Check out our issues labeled [`good first issue`](https://github.com/agentic-evolution/harness/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)!

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
