"""Additional integration tests for Typer CLI commands to maximize branch coverage."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harness.cli.main import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Agentic Evolution Harness v" in result.stdout


def test_cli_list_plugins_all() -> None:
    result = runner.invoke(app, ["list-plugins"])
    assert result.exit_code == 0
    assert "exact_match" in result.stdout
    assert "success_rate" in result.stdout


def test_cli_list_plugins_filtered() -> None:
    result = runner.invoke(app, ["list-plugins", "evaluators"])
    assert result.exit_code == 0
    assert "exact_match" in result.stdout


def test_cli_validate_success(tmp_path: Path) -> None:
    bm_file = tmp_path / "valid.yaml"
    bm_file.write_text("name: valid-bm\ntests: []\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(bm_file)])
    assert result.exit_code == 0
    assert "Benchmark configuration is valid" in result.stdout


def test_cli_validate_failure(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("random text", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(bad_file)])
    assert result.exit_code == 1


def test_cli_evaluate_formats(tmp_path: Path) -> None:
    bm_path = Path("examples/basic/benchmark.yaml")
    out_json = tmp_path / "run.json"

    # Test Markdown format
    res_md = runner.invoke(
        app,
        [
            "evaluate",
            str(bm_path),
            "--output",
            str(out_json),
            "--format",
            "markdown",
            "--no-thresholds",
        ],
    )
    assert res_md.exit_code == 0
    assert "# Evaluation Report:" in res_md.stdout

    # Test JSON format
    res_json = runner.invoke(
        app,
        [
            "evaluate",
            str(bm_path),
            "--output",
            str(out_json),
            "--format",
            "json",
            "--no-thresholds",
        ],
    )
    assert res_json.exit_code == 0
    assert '"basic-support-benchmark"' in res_json.stdout


def test_cli_evaluate_threshold_violation(tmp_path: Path) -> None:
    # Benchmark requiring 100% success rate when agent gets 80%
    yaml_content = """
name: "strict-benchmark"
agent:
  adapter: generic
  module: "examples.basic.mock_agent:support_agent"
thresholds:
  success_rate:
    minimum: 1.00
tests:
  - id: t1
    name: greeting
    input: "hello"
    expected: "Hello! How can I assist you with your order today?"
  - id: t2
    name: fail_test
    input: "unknown"
    expected: "Something impossible"
"""
    bm_file = tmp_path / "strict.yaml"
    bm_file.write_text(yaml_content, encoding="utf-8")

    result = runner.invoke(app, ["evaluate", str(bm_file), "--thresholds"])
    assert result.exit_code == 1
    assert "REGRESSION THRESHOLD VIOLATION DETECTED" in result.stdout


def test_cli_compare_with_regression() -> None:
    v1_file = Path("examples/basic/v2_improved.json")
    v2_file = Path("examples/basic/v1_baseline.json")

    # Comparing improved as baseline vs worse as candidate triggers regression exit code 1
    result = runner.invoke(app, ["compare", str(v1_file), str(v2_file), "--fail-on-regression"])
    assert result.exit_code == 1
    assert "Comparison detected regressions" in result.stdout
