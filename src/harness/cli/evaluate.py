"""CLI command to run benchmark evaluation."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from harness.adapters.base import AdapterRegistry
from harness.adapters.generic import GenericAgent
from harness.adapters.mock import MockAgent
from harness.benchmarks.loader import BenchmarkLoader
from harness.comparison.regression import RegressionDetector
from harness.core.agent import Agent
from harness.reporters.console import ConsoleReporter
from harness.reporters.json import JSONReporter
from harness.reporters.markdown import MarkdownReporter
from harness.runner.runner import AgentRunner

console = Console()


def run_evaluate(
    benchmark_path: Path = typer.Argument(
        ...,
        help="Path to benchmark YAML or JSON file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    agent_override: str | None = typer.Option(
        None,
        "--agent",
        "-a",
        help="Optional module:callable override for the agent under test.",
    ),
    output_path: Path | None = typer.Option(
        Path("results/latest.json"),
        "--output",
        "-o",
        help="Output file path for the experiment JSON artifact.",
    ),
    report_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Reporting format: console, json, or markdown.",
    ),
    enforce_thresholds: bool = typer.Option(
        True,
        "--thresholds/--no-thresholds",
        help="Enforce regression thresholds defined in benchmark file.",
    ),
) -> None:
    """Execute evaluation for a given benchmark file against an AI agent."""
    try:
        benchmark = BenchmarkLoader.load(benchmark_path)
    except Exception as exc:
        console.print(f"[bold red]Failed to load benchmark:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    # Determine agent instance
    agent_target = agent_override or benchmark.agent.module
    adapter_name = benchmark.agent.adapter.lower()

    agent: Agent
    if agent_target:
        agent = GenericAgent(target=agent_target, **benchmark.agent.config)
    elif adapter_name == "mock":
        agent = MockAgent(**benchmark.agent.config)
    else:
        try:
            agent = AdapterRegistry.get(adapter_name, **benchmark.agent.config)
        except Exception:
            # Fallback to mock agent with default responses for easy starter onboarding
            agent = MockAgent(default_output="Default response")

    # Build runner
    runner = AgentRunner(
        agent=agent,
        default_evaluators=benchmark.evaluators if benchmark.evaluators else ["exact_match"],
        metrics=benchmark.metrics if benchmark.metrics else ["success_rate", "accuracy", "latency"],
    )

    experiment = runner.run(
        test_cases=benchmark.tests,
        experiment_name=benchmark.name,
        benchmark_info={"file": str(benchmark_path), "description": benchmark.description},
    )

    # Persist JSON artifact
    if output_path is not None:
        JSONReporter().report(experiment, destination=output_path)

    # Render Report
    if report_format == "console":
        ConsoleReporter(console=console).report(experiment, destination=output_path)
    elif report_format == "markdown":
        md_text = MarkdownReporter().report(experiment)
        console.print(md_text)
    elif report_format == "json":
        json_text = JSONReporter().report(experiment)
        console.print(json_text)

    # Regression threshold check
    if enforce_thresholds and benchmark.thresholds:
        report = RegressionDetector.check_thresholds(experiment, benchmark.thresholds)
        if not report.passed:
            console.print("\n[bold red]🚨 REGRESSION THRESHOLD VIOLATION DETECTED:[/bold red]")
            for violation in report.violations:
                console.print(f"  [red]• {violation.message}[/red]")
            raise typer.Exit(code=1)
