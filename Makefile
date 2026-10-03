.PHONY: help install dev test test-cov lint format typecheck check clean

help:
	@echo "Available commands:"
	@echo "  install    Install dependencies using uv"
	@echo "  dev        Install package in editable mode with dev dependencies"
	@echo "  test       Run unit and integration tests"
	@echo "  test-cov   Run tests with coverage reporting"
	@echo "  lint       Check code quality with ruff"
	@echo "  format     Format code with ruff"
	@echo "  typecheck  Run mypy type checker"
	@echo "  check      Run lint, typecheck, and test suite"
	@echo "  clean      Remove temporary and cache files"

install:
	uv sync

dev:
	uv sync --all-extras

test:
	uv run pytest

test-cov:
	uv run pytest --cov=harness --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy src

check: lint typecheck test

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
