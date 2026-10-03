"""Unit tests for built-in evaluators."""

from __future__ import annotations

from harness.core.agent import AgentOutput
from harness.core.testcase import TestCase
from harness.core.trace import ToolCallRecord
from harness.evaluators.contains import ContainsEvaluator
from harness.evaluators.exact_match import ExactMatchEvaluator
from harness.evaluators.json_match import JSONMatchEvaluator
from harness.evaluators.tool_usage import ToolUsageEvaluator


def test_exact_match_evaluator_success() -> None:
    evaluator = ExactMatchEvaluator()
    tc = TestCase(id="1", name="exact", input="hi", expected="Hello World")
    out = AgentOutput(output="  Hello World  ")
    result = evaluator.evaluate(tc, out)
    assert result.passed
    assert result.score == 1.0


def test_exact_match_evaluator_no_expected() -> None:
    evaluator = ExactMatchEvaluator()
    tc = TestCase(id="1", name="exact", input="hi", expected=None)
    out = AgentOutput(output="Hello")
    result = evaluator.evaluate(tc, out)
    assert result.passed


def test_exact_match_evaluator_agent_error() -> None:
    evaluator = ExactMatchEvaluator()
    tc = TestCase(id="1", name="exact", input="hi", expected="Hello")
    out = AgentOutput(output="", error="Fatal exception")
    result = evaluator.evaluate(tc, out)
    assert not result.passed
    assert "Agent produced an error" in result.explanation


def test_exact_match_evaluator_case_sensitive() -> None:
    evaluator = ExactMatchEvaluator(ignore_case=False)
    tc = TestCase(id="1", name="exact", input="hi", expected="HELLO")
    out = AgentOutput(output="hello")
    result = evaluator.evaluate(tc, out)
    assert not result.passed
    assert result.score == 0.0

    evaluator_ci = ExactMatchEvaluator(ignore_case=True)
    result_ci = evaluator_ci.evaluate(tc, out)
    assert result_ci.passed


def test_contains_evaluator_substring_and_regex() -> None:
    evaluator = ContainsEvaluator(substring="order #123")
    tc = TestCase(id="1", name="contains", input="in", expected=None)
    out = AgentOutput(output="Confirmed order #123 is ready.")
    res = evaluator.evaluate(tc, out)
    assert res.passed

    # Regex test
    evaluator_rx = ContainsEvaluator(substring=r"\d{3}-\d{2}", is_regex=True)
    out_rx = AgentOutput(output="ID: 999-12 approved")
    res_rx = evaluator_rx.evaluate(tc, out_rx)
    assert res_rx.passed

    # Regex failure
    out_bad = AgentOutput(output="ID: ABC approved")
    res_bad = evaluator_rx.evaluate(tc, out_bad)
    assert not res_bad.passed

    # Invalid regex pattern handling
    evaluator_inv = ContainsEvaluator(substring="[unclosed-bracket", is_regex=True)
    res_inv = evaluator_inv.evaluate(tc, out_rx)
    assert not res_inv.passed
    assert "Invalid regular expression" in res_inv.explanation


def test_contains_evaluator_agent_error() -> None:
    evaluator = ContainsEvaluator(substring="test")
    tc = TestCase(id="1", name="contains", input="in")
    out = AgentOutput(output="", error="Network failure")
    res = evaluator.evaluate(tc, out)
    assert not res.passed


def test_json_match_evaluator_subset_and_lists() -> None:
    evaluator = JSONMatchEvaluator(subset=True, ignore_order=True)
    tc = TestCase(
        id="1",
        name="json",
        input="in",
        expected={"status": "ok", "items": ["apple", "banana"]},
    )
    # Actual has extra field and list in different order
    out = AgentOutput(output='{"status": "ok", "items": ["banana", "apple"], "extra": 42}')
    res = evaluator.evaluate(tc, out)
    assert res.passed
    assert res.score == 1.0

    # Malformed JSON handling
    bad_out = AgentOutput(output="Not a JSON string")
    bad_res = evaluator.evaluate(tc, bad_out)
    assert not bad_res.passed
    assert "not valid JSON" in bad_res.explanation


def test_json_match_markdown_code_block() -> None:
    evaluator = JSONMatchEvaluator()
    tc = TestCase(id="1", name="json", input="in", expected={"key": "val"})
    out = AgentOutput(output='```json\n{\n  "key": "val"\n}\n```')
    res = evaluator.evaluate(tc, out)
    assert res.passed


def test_tool_usage_evaluator_trajectories() -> None:
    evaluator = ToolUsageEvaluator(
        expected_tools=["search_db", "send_email"],
        ordered=True,
        forbidden_tools=["drop_table"],
        validate_args={"send_email": {"to": "alice@example.com"}},
    )

    tc = TestCase(id="1", name="tools", input="in")

    # Positive test
    tools = [
        ToolCallRecord(tool_name="search_db", args={"query": "users"}),
        ToolCallRecord(tool_name="send_email", args={"to": "alice@example.com", "body": "hi"}),
    ]
    out = AgentOutput(output="Done", tool_calls=tools)
    res = evaluator.evaluate(tc, out)
    assert res.passed

    # Forbidden tool test
    bad_tools = [
        ToolCallRecord(tool_name="search_db", args={}),
        ToolCallRecord(tool_name="drop_table", args={}),
    ]
    out_bad = AgentOutput(output="Done", tool_calls=bad_tools)
    res_bad = evaluator.evaluate(tc, out_bad)
    assert not res_bad.passed
    assert "Forbidden tool" in res_bad.explanation

    # Out of order test
    reversed_tools = [
        ToolCallRecord(tool_name="send_email", args={"to": "alice@example.com"}),
        ToolCallRecord(tool_name="search_db", args={}),
    ]
    out_rev = AgentOutput(output="Done", tool_calls=reversed_tools)
    res_rev = evaluator.evaluate(tc, out_rev)
    assert not res_rev.passed
    assert "out of expected order" in res_rev.explanation

    # Argument mismatch
    arg_mismatch_tools = [
        ToolCallRecord(tool_name="search_db", args={}),
        ToolCallRecord(tool_name="send_email", args={"to": "bob@example.com"}),
    ]
    out_arg_mismatch = AgentOutput(output="Done", tool_calls=arg_mismatch_tools)
    res_arg = evaluator.evaluate(tc, out_arg_mismatch)
    assert not res_arg.passed
    assert "Argument mismatch" in res_arg.explanation
