"""CLI command to compare two experiment evaluation runs."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harness.comparison.comparator import ExperimentComparator
from harness.core.experiment import Experiment

console = Console()


def run_compare(
    baseline_path: Path = typer.Argument(
        ...,
        help="Path to baseline experiment JSON artifact (v1).",
        exists=True,
        file_okay=True,
        readable=True,
    ),
    candidate_path: Path = typer.Argument(
        ...,
        help="Path to candidate experiment JSON artifact (v2).",
        exists=True,
        file_okay=True,
        readable=True,
    ),
    fail_on_regression: bool = typer.Option(
        True,
        "--fail-on-regression/--allow-regression",
        help="Exit with code 1 if any metric regresses.",
    ),
) -> None:
    """Compare two experiment runs and display performance delta."""
    try:
        base_exp = Experiment.model_validate(json.loads(baseline_path.read_text(encoding="utf-8")))
        cand_exp = Experiment.model_validate(json.loads(candidate_path.read_text(encoding="utf-8")))
    except Exception as exc:
        console.print(f"[bold red]Failed to load experiment artifacts:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    comparison = ExperimentComparator.compare(base_exp, cand_exp)

    banner = Panel(
        f"[bold cyan]Experiment Comparison[/bold cyan]\n"
        f"[dim]Baseline: {comparison.baseline_name} ({comparison.baseline_id})[/dim]\n"
        f"[dim]Candidate: {comparison.candidate_name} ({comparison.candidate_id})[/dim]",
        box=ROUNDED,
        expand=False,
    )
    console.print(banner)

    # Metrics Delta Table
    table = Table(box=ROUNDED, title="Metric Comparison")
    table.add_column("Metric", style="bold")
    table.add_column("Baseline (v1)", justify="right")
    table.add_column("Candidate (v2)", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Evaluation", justify="center")

    has_regression = False

    for delta in comparison.deltas.values():
        sign = "+" if delta.delta > 0 else ""
        if delta.is_improvement:
            eval_tag = "[green]▲ Improvement[/green]"
            delta_str = f"[green]{sign}{delta.delta:.4f}[/green]"
            if delta.pct_delta is not None:
                delta_str += f" [green]({delta.pct_delta:+.1f}%)[/green]"
        elif delta.is_regression:
            eval_tag = "[red]▼ Regression[/red]"
            delta_str = f"[red]{sign}{delta.delta:.4f}[/red]"
            if delta.pct_delta is not None:
                delta_str += f" [red]({delta.pct_delta:+.1f}%)[/red]"
            has_regression = True
        else:
            eval_tag = "[dim]• Neutral[/dim]"
            delta_str = f"[dim]{sign}{delta.delta:.4f}[/dim]"

        table.add_row(
            delta.name.replace("_", " ").title(),
            delta.v1_formatted,
            delta.v2_formatted,
            delta_str,
            eval_tag,
        )

    console.print(table)

    if comparison.newly_passed_tests:
        console.print(
            f"[green]Newly passing tests ({len(comparison.newly_passed_tests)}):[/green] "
            + ", ".join(comparison.newly_passed_tests)
        )

    if comparison.newly_failed_tests:
        console.print(
            f"[red]Newly failing tests ({len(comparison.newly_failed_tests)}):[/red] "
            + ", ".join(comparison.newly_failed_tests)
        )

    if has_regression and fail_on_regression:
        console.print("\n[bold red]Comparison detected regressions in candidate run.[/bold red]")
        raise typer.Exit(code=1)
