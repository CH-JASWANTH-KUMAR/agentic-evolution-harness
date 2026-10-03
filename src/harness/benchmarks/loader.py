"""Benchmark loader supporting YAML and JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from harness.benchmarks.schema import BenchmarkConfig


class BenchmarkLoader:
    """Loads and validates benchmark configurations from files or directories."""

    @classmethod
    def load(cls, file_path: str | Path) -> BenchmarkConfig:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Benchmark file not found: {path}")

        content = path.read_text(encoding="utf-8")
        data: dict[str, Any]

        if path.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(content) or {}
        elif path.suffix.lower() == ".json":
            data = json.loads(content)
        else:
            raise ValueError(
                f"Unsupported benchmark format: '{path.suffix}'. Use .yaml, .yml, or .json."
            )

        return BenchmarkConfig.model_validate(data)

    @classmethod
    def validate_file(cls, file_path: str | Path) -> tuple[bool, str]:
        """Validate a benchmark file, returning (is_valid, message)."""
        try:
            cls.load(file_path)
            return True, "Valid benchmark configuration"
        except Exception as exc:
            return False, str(exc)
