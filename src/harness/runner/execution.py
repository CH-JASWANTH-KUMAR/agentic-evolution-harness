"""Execution timing and context helpers."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager


class ExecutionTimer:
    """Timer utility to record execution durations."""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def start(self) -> None:
        self.start_time = time.perf_counter()

    def stop(self) -> float:
        self.end_time = time.perf_counter()
        return self.duration

    @property
    def duration(self) -> float:
        if self.end_time >= self.start_time:
            return self.end_time - self.start_time
        return time.perf_counter() - self.start_time


@contextmanager
def measure_time() -> Iterator[ExecutionTimer]:
    """Context manager measuring execution duration."""
    timer = ExecutionTimer()
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()
