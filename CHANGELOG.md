# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-03

### Added
- **Core Domain**:
  - `Agent` protocol and `AgentOutput` model supporting output, latency, token usage, cost, and tool calls.
  - `TestCase` and `EvaluatorConfig` schema with YAML/JSON validation.
  - `Trace` and `ToolCallRecord` models for trajectory tracking.
  - `EvaluationResult` and `TestCaseResult` with normalized scoring.
  - `Experiment` model and persistence.
- **Built-in Evaluators**:
  - `ExactMatchEvaluator`: strict string matching with whitespace and case options.
  - `ContainsEvaluator`: substring inclusion and regex pattern support.
  - `JSONMatchEvaluator`: semantic JSON matching with subset and list order controls.
  - `ToolUsageEvaluator`: trajectory, ordering, forbidden tool, and argument validation.
- **Built-in Metrics**:
  - `SuccessRateMetric`: percentage of passing tests.
  - `AccuracyMetric`: mean evaluation score.
  - `LatencyMetric`: mean execution latency.
  - `CostMetric`: total and average monetary cost.
  - `ReliabilityMetric`: error-free execution rate.
- **Adapters**:
  - `MockAgent`: deterministic agent with customizable outputs, latencies, and tool calls.
  - `GenericAgent`: dynamic Python function/class loader.
  - `SubprocessAgent`: CLI execution adapter.
- **Reporters**:
  - `ConsoleReporter`: Rich terminal dashboard with progress and metric cards.
  - `JSONReporter`: standardized JSON experiment serialization.
  - `MarkdownReporter`: GitHub-flavored markdown report generator.
- **Comparison & Evolution**:
  - `ExperimentComparator`: directional delta mathematics between experiment runs.
  - `RegressionDetector`: CI threshold checking and violation reporting.
- **CLI Commands**:
  - `harness evaluate`: run benchmark evaluations.
  - `harness compare`: compare two experiment runs.
  - `harness validate`: validate benchmark syntax and schemas.
  - `harness list-plugins`: inspect registered evaluators, metrics, adapters, and reporters.
- **Documentation & Community**:
  - Comprehensive `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
  - Issue templates and Pull Request template.
  - 90% branch coverage unit and integration test suite.
