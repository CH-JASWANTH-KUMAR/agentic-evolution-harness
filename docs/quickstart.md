# Quickstart Guide

Get up and running with **Agentic Evolution Harness** in 5 minutes.

---

## 1. Installation

```bash
git clone https://github.com/agentic-evolution/harness.git
cd harness
uv sync
```

---

## 2. Define an Agent

Create a file named `my_agent.py`:

```python
from harness.core.agent import AgentOutput
from harness.core.trace import ToolCallRecord


def answer_query(user_input: str) -> AgentOutput:
    if "refund" in user_input.lower():
        tools = [ToolCallRecord(tool_name="process_refund", args={"amount": 25.0})]
        return AgentOutput(
            output="Refund of $25.00 has been initiated.",
            tool_calls=tools,
        )
    return AgentOutput(output="How can I help you today?")
```

---

## 3. Define a Benchmark

Create a benchmark file named `my_benchmark.yaml`:

```yaml
version: "1.0"
name: "my-first-benchmark"

agent:
  adapter: generic
  module: "my_agent:answer_query"

evaluators:
  - name: exact_match

metrics:
  - success_rate
  - latency

thresholds:
  success_rate:
    minimum: 1.0

tests:
  - id: test-01
    name: "refund_intent"
    input: "I need a refund for my last order."
    expected: "Refund of $25.00 has been initiated."
    evaluators:
      - name: contains
        options:
          substring: "Refund of $25.00"
      - name: tool_usage
        options:
          expected_tools: ["process_refund"]
```

---

## 4. Run the Evaluation

```bash
uv run harness evaluate my_benchmark.yaml
```

You'll see a terminal summary and the complete experiment artifact saved to `results/latest.json`.

---

## 5. Compare Agent Iterations

Modify your agent prompt or code, then run:

```bash
# Save baseline
uv run harness evaluate my_benchmark.yaml --output results/v1.json

# Modify your agent... and run candidate evaluation
uv run harness evaluate my_benchmark.yaml --output results/v2.json

# Compare the two versions
uv run harness compare results/v1.json results/v2.json
```
