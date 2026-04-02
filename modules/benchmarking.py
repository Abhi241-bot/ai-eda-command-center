"""
benchmarking.py
───────────────
Measures runtime, memory usage, and scalability for each EDA tool,
providing objective performance data for the recommendation engine.
"""

from __future__ import annotations

import gc
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

import numpy as np
import pandas as pd
import psutil

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    tool: str
    dataset_rows: int
    dataset_cols: int
    duration_sec: float
    peak_memory_mb: float
    memory_delta_mb: float
    status: str
    scalability: list[dict] = field(default_factory=list)  # per-fraction results

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _process_memory_mb() -> float:
    proc = psutil.Process(os.getpid())
    return round(proc.memory_info().rss / 1e6, 2)


def benchmark_tool(
    runner_fn: Callable[[pd.DataFrame, str], dict],
    df: pd.DataFrame,
    output_dir: str,
    tool_name: str,
    timeout_sec: int = 300,
) -> BenchmarkResult:
    """
    Run *runner_fn* on *df*, capturing wall-clock time and peak memory.

    Parameters
    ----------
    runner_fn    : e.g. eda_runner.run_ydata
    df           : Input DataFrame
    output_dir   : Where the tool writes its report
    tool_name    : String label
    timeout_sec  : Abort if exceeded (soft check post-run)
    """
    gc.collect()
    mem_before = _process_memory_mb()
    peak_mem = mem_before

    t_start = time.perf_counter()
    status = "success"
    try:
        result = runner_fn(df, output_dir)
        status = result.get("status", "success")
    except Exception as e:
        logger.error("Benchmark run failed for %s: %s", tool_name, e)
        status = f"error: {e}"
    finally:
        gc.collect()

    duration = time.perf_counter() - t_start
    mem_after = _process_memory_mb()
    peak_mem = max(peak_mem, mem_after)

    if duration > timeout_sec:
        logger.warning("%s exceeded timeout (%ds > %ds).", tool_name, duration, timeout_sec)
        status = f"timeout ({duration:.0f}s)"

    return BenchmarkResult(
        tool=tool_name,
        dataset_rows=len(df),
        dataset_cols=len(df.columns),
        duration_sec=round(duration, 3),
        peak_memory_mb=round(peak_mem, 2),
        memory_delta_mb=round(mem_after - mem_before, 2),
        status=status,
    )


def run_scalability_test(
    runner_fn: Callable,
    df: pd.DataFrame,
    output_dir: str,
    tool_name: str,
    fractions: list[float] | None = None,
) -> list[dict[str, Any]]:
    """
    Run *runner_fn* on subsets of *df* at specified *fractions*.

    Returns
    -------
    list of dicts with keys: fraction, n_rows, duration_sec, memory_delta_mb, status
    """
    if fractions is None:
        from config import SCALABILITY_FRACTIONS  # type: ignore
        fractions = SCALABILITY_FRACTIONS

    results: list[dict[str, Any]] = []
    for frac in fractions:
        n = max(10, int(len(df) * frac))
        subset = df.sample(n=n, random_state=42).reset_index(drop=True)
        logger.info("Scalability test: %s @ %.0f%% (%d rows)", tool_name, frac * 100, n)
        bm = benchmark_tool(runner_fn, subset, output_dir + f"_scale_{int(frac*100)}", tool_name)
        results.append({
            "fraction": frac,
            "n_rows": n,
            "duration_sec": bm.duration_sec,
            "memory_delta_mb": bm.memory_delta_mb,
            "status": bm.status,
        })
    return results


def benchmark_all_tools(
    df: pd.DataFrame,
    reports_base: str,
    enabled_tools: dict[str, bool] | None = None,
) -> dict[str, BenchmarkResult]:
    """
    Benchmark all enabled EDA tools and return a dict of BenchmarkResult.
    """
    from modules.eda_runner import TOOL_RUNNERS  # type: ignore
    if enabled_tools is None:
        from config import TOOLS_ENABLED, BENCHMARK_TIMEOUT_SEC  # type: ignore
        enabled_tools = TOOLS_ENABLED
    else:
        from config import BENCHMARK_TIMEOUT_SEC  # type: ignore

    results: dict[str, BenchmarkResult] = {}
    for tool_name, enabled in enabled_tools.items():
        if not enabled:
            results[tool_name] = BenchmarkResult(
                tool=tool_name,
                dataset_rows=len(df), dataset_cols=len(df.columns),
                duration_sec=0.0, peak_memory_mb=0.0, memory_delta_mb=0.0,
                status="disabled",
            )
            continue
        runner = TOOL_RUNNERS.get(tool_name)
        if runner is None:
            continue
        out_dir = f"{reports_base}/{tool_name}"
        bm = benchmark_tool(runner, df, out_dir, tool_name, BENCHMARK_TIMEOUT_SEC)
        results[tool_name] = bm

    return results
