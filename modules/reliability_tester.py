"""
reliability_tester.py
──────────────────────
Evaluates EDA tool robustness under messy real-world data conditions:
  - High missing values
  - Noisy data
  - Imbalanced class distributions
  - High-cardinality categorical variables
"""

from __future__ import annotations

import logging
import random
import string
from typing import Any, Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─── Dataset Degradation Helpers ─────────────────────────────────────────────────

def inject_missing(df: pd.DataFrame, rate: float = 0.30) -> pd.DataFrame:
    """Randomly set *rate* fraction of values to NaN."""
    df = df.copy()
    n_total = df.size
    n_missing = int(n_total * rate)
    flat_idxs = random.sample(range(n_total), n_missing)
    for idx in flat_idxs:
        row, col = divmod(idx, len(df.columns))
        df.iat[row, col] = np.nan
    return df


def inject_noise(df: pd.DataFrame, noise_std_multiplier: float = 0.5) -> pd.DataFrame:
    """Add Gaussian noise to numeric columns."""
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        std = df[col].std(skipna=True) or 1.0
        df[col] = df[col] + np.random.normal(0, std * noise_std_multiplier, size=len(df))
    return df


def create_imbalanced(df: pd.DataFrame, minority_frac: float = 0.05) -> pd.DataFrame:
    """
    If a binary target column exists (last column with 2 unique values),
    drastically reduce the minority class to *minority_frac*.
    """
    df = df.copy()
    target_col = df.columns[-1]
    if df[target_col].nunique() != 2:
        return df  # Not binary — skip
    classes = df[target_col].value_counts()
    minority_class = classes.idxmin()
    majority_class = classes.idxmax()
    n_majority = classes[majority_class]
    n_minority_desired = max(1, int(n_majority * minority_frac / (1 - minority_frac)))
    minority_rows = df[df[target_col] == minority_class].sample(
        n=min(n_minority_desired, len(df[df[target_col] == minority_class])),
        random_state=42,
    )
    majority_rows = df[df[target_col] == majority_class]
    return pd.concat([majority_rows, minority_rows]).sample(frac=1, random_state=42).reset_index(drop=True)


def inject_high_cardinality(df: pd.DataFrame, n_unique: int = 500) -> pd.DataFrame:
    """Add a high-cardinality random string column (always adds, never replaces)."""
    df = df.copy()
    # Always add a brand-new column so shape[1] increases
    df["hc_token"] = [
        "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        for _ in range(len(df))
    ]
    # Also overwrite first categorical col if one exists (for realism)
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        col = cat_cols[0]
        df[col] = [
            "".join(random.choices(string.ascii_lowercase, k=6)) for _ in range(len(df))
        ]
    return df


# ─── Scenario Runner ─────────────────────────────────────────────────────────────

SCENARIOS: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "clean_baseline":     lambda df: df.copy(),
    "missing_low_10pct":  lambda df: inject_missing(df, rate=0.10),
    "missing_high_40pct": lambda df: inject_missing(df, rate=0.40),
    "noisy_data":         inject_noise,
    "imbalanced_5pct":    lambda df: create_imbalanced(df, minority_frac=0.05),
    "high_cardinality":   inject_high_cardinality,
}


def run_reliability_suite(
    df: pd.DataFrame,
    runner_fn: Callable[[pd.DataFrame, str], dict],
    output_base: str,
    tool_name: str,
    max_rows: int = 5000,
) -> list[dict[str, Any]]:
    """
    Run *runner_fn* under all degradation scenarios.

    Automatically caps the dataset at *max_rows* for reliability testing
    to ensure the suite completes in a reasonable time.

    Returns
    -------
    list of dicts: scenario, status, duration_sec, memory_delta_mb, notes
    """
    # Cap rows for reliability speed
    test_df = df.head(max_rows) if len(df) > max_rows else df.copy()

    results: list[dict[str, Any]] = []
    for scenario_name, transform in SCENARIOS.items():
        logger.info("Reliability [%s] — scenario: %s", tool_name, scenario_name)
        try:
            degraded_df = transform(test_df)
            out_dir = f"{output_base}/{tool_name}_{scenario_name}"
            run_result = runner_fn(degraded_df, out_dir)
            results.append({
                "scenario": scenario_name,
                "status": run_result.get("status", "unknown"),
                "duration_sec": run_result.get("duration_sec", 0),
                "memory_delta_mb": run_result.get("memory_delta_mb", 0),
                "n_rows": len(degraded_df),
                "notes": run_result.get("status", ""),
            })
        except Exception as e:
            logger.error("Reliability scenario %s failed: %s", scenario_name, e)
            results.append({
                "scenario": scenario_name,
                "status": f"error: {e}",
                "duration_sec": 0,
                "memory_delta_mb": 0,
                "n_rows": len(test_df),
                "notes": str(e),
            })
    return results


def reliability_summary(
    all_results: dict[str, list[dict]],
) -> dict[str, Any]:
    """
    Summarise reliability results across tools.

    Returns
    -------
    dict: {tool: {pass_count, fail_count, pass_rate, slowest_scenario}}
    """
    summary: dict[str, Any] = {}
    for tool, results in all_results.items():
        passes = [r for r in results if r["status"] == "success"]
        fails = [r for r in results if r["status"] != "success"]
        slowest = max(results, key=lambda x: x.get("duration_sec", 0), default={})
        summary[tool] = {
            "pass_count": len(passes),
            "fail_count": len(fails),
            "total_scenarios": len(results),
            "pass_rate": round(len(passes) / max(len(results), 1) * 100, 1),
            "slowest_scenario": slowest.get("scenario", "N/A"),
            "slowest_sec": slowest.get("duration_sec", 0),
        }
    return summary
