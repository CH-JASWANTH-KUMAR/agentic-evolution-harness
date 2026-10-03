"""CLI command to validate benchmark configuration syntax and schema."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from harness.benchmarks.loader import BenchmarkLoader

console = Console()


def run_validate(
    benchmark_path: Path = typer.Argument(
        ...,
        help="Path to benchmark file to validate.",
        exists=True,
        file_okay=True,
        readable=True,
    ),
) -> None:
    """Validate a benchmark configuration without executing tests."""
    is_valid, message = BenchmarkLoader.validate_file(benchmark_path)
    if is_valid:
        cfg = BenchmarkLoader.load(benchmark_path)
        console.print("[bold green]✓ Benchmark configuration is valid![/bold green]")
        console.print(f"  • Name: [bold]{cfg.name}[/bold]")
        console.print(f"  • Test Cases: [bold]{len(cfg.tests)}[/bold]")
        console.print(f"  • Evaluators: [bold]{len(cfg.evaluators)}[/bold]")
        console.print(f"  • Metrics: [bold]{len(cfg.metrics)}[/bold]")
    else:
        console.print(f"[bold red]✗ Benchmark validation failed:[/bold red] {message}")
        raise typer.Exit(code=1)
