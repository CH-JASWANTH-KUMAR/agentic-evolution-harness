"""Integration tests for the complete end-to-end evaluation pipeline."""

from __future__ import annotations

from pathlib import Path

from harness.adapters.mock import MockAgent
from harness.benchmarks.loader import BenchmarkLoader
from harness.runner.runner import AgentRunner


def test_end_to_end_benchmark_run(tmp_path: Path) -> None:
    # 1. Create a dynamic benchmark file
    yaml_content = """
version: "1.0"
name: "integration-benchmark"
evaluators:
  - name: exact_match
metrics:
  - success_rate
  - latency
tests:
  - id: "t1"
    name: "ping_test"
    input: "ping"
    expected: "pong"
  - id: "t2"
    name: "math_test"
    input: "2+2"
    expected: "4"
"""
    bm_file = tmp_path / "test_bm.yaml"
    bm_file.write_text(yaml_content, encoding="utf-8")

    # 2. Load benchmark
    benchmark = BenchmarkLoader.load(bm_file)
    assert benchmark.name == "integration-benchmark"
    assert len(benchmark.tests) == 2

    # 3. Configure mock agent
    agent = MockAgent(responses={"ping": "pong", "2+2": "4"})

    # 4. Execute with runner
    runner = AgentRunner(
        agent=agent,
        default_evaluators=benchmark.evaluators,
        metrics=benchmark.metrics,
    )

    exp = runner.run(test_cases=benchmark.tests, experiment_name=benchmark.name)

    # 5. Assert outcomes
    assert exp.total_tests == 2
    assert exp.passed_tests == 2
    assert exp.success_rate == 1.0
    assert "success_rate" in exp.metrics
    assert exp.metrics["success_rate"].value == 1.0
