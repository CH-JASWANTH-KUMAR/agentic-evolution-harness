"""Unit tests for core data models and protocols."""

from __future__ import annotations

from harness.core.agent import AgentOutput
from harness.core.experiment import Experiment, MetricResult
from harness.core.result import EvaluationResult, TestCaseResult
from harness.core.testcase import EvaluatorConfig, TestCase
from harness.core.trace import ToolCallRecord, Trace


def test_agent_output_properties() -> None:
    out = AgentOutput(output="Hello World", latency=1.2, error=None)
    assert not out.is_error
    assert out.text == "Hello World"

    dict_out = AgentOutput(output={"key": "val"})
    assert '"key": "val"' in dict_out.text

    err_out = AgentOutput(output="", error="Fatal timeout")
    assert err_out.is_error


def test_test_case_model() -> None:
    tc = TestCase(
        id="test-1",
        name="simple_test",
        input="What is 2+2?",
        expected="4",
        evaluators=[EvaluatorConfig(name="exact_match")],
        tags=["math"],
    )
    assert tc.id == "test-1"
    assert tc.input_text == "What is 2+2?"
    assert len(tc.evaluators) == 1


def test_test_case_result_average_score() -> None:
    tc = TestCase(id="t1", name="t1", input="in", expected="exp")
    out = AgentOutput(output="out")
    res = TestCaseResult(
        test_case=tc,
        output=out,
        evaluations=[
            EvaluationResult(evaluator="e1", score=1.0, passed=True),
            EvaluationResult(evaluator="e2", score=0.5, passed=False),
        ],
        passed=False,
        duration=0.5,
    )
    assert res.average_score == 0.75
    assert not res.passed


def test_experiment_summary_properties() -> None:
    tc1 = TestCase(id="t1", name="t1", input="in1")
    tc2 = TestCase(id="t2", name="t2", input="in2")

    res1 = TestCaseResult(test_case=tc1, output=AgentOutput(), passed=True, duration=0.1)
    res2 = TestCaseResult(test_case=tc2, output=AgentOutput(), passed=False, duration=0.2)

    exp = Experiment(
        id="exp-01",
        name="test_experiment",
        results=[res1, res2],
        metrics={"acc": MetricResult(name="acc", value=0.5, formatted_value="50%")},
    )

    assert exp.total_tests == 2
    assert exp.passed_tests == 1
    assert exp.failed_tests == 1
    assert exp.success_rate == 0.5


def test_trace_and_tool_call_records() -> None:
    tool = ToolCallRecord(
        tool_name="calculator",
        args={"operation": "add", "a": 5, "b": 7},
        output=12,
        duration=0.01,
        status="success",
    )
    trace = Trace(tool_calls=[tool])
    assert len(trace.tool_calls) == 1
    assert trace.tool_calls[0].tool_name == "calculator"
