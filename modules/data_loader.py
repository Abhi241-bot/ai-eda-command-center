"""
data_loader.py
─────────────
Loads and profile-validates CSV datasets.
Returns a clean DataFrame and a structured metadata dict.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─── Public API ──────────────────────────────────────────────────────────────────

def load_dataset(path: str | Path) -> pd.DataFrame:
    """
    Read a CSV file from *path* and return a cleaned DataFrame.
    Raises FileNotFoundError / ValueError on bad input.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    if path.suffix.lower() not in {".csv", ".tsv"}:
        raise ValueError(f"Only CSV/TSV files are supported. Got: {path.suffix}")

    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    df = pd.read_csv(path, sep=sep, low_memory=False)
    logger.info("Loaded dataset %s — shape: %s", path.name, df.shape)
    return df


def sanitize_val(v: Any) -> Any:
    """Recursively sanitize dicts/lists for JSON compliance (NaN/Inf -> None/0.0)."""
    if isinstance(v, dict):
        return {k: sanitize_val(v2) for k, v2 in v.items()}
    elif isinstance(v, (list, tuple)):
        return [sanitize_val(v2) for v2 in v]
    elif pd.isna(v):
        return None
    elif isinstance(v, (np.float64, np.float32, float)):
        if np.isinf(v):
            return 0.0
        return float(v)
    elif isinstance(v, (np.int64, np.int32, int)):
        return int(v)
    return v


def get_dataset_profile(df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute a lightweight metadata profile of a DataFrame.

    Returns
    -------
    dict with keys:
        n_rows, n_cols, numeric_cols, categorical_cols, bool_cols,
        missing_counts, missing_pct, cardinality, class_distribution (if binary),
        memory_mb, dtypes, skewness, has_target_hint
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    bool_cols = df.select_dtypes(include=["bool"]).columns.tolist()

    missing_counts: dict[str, int] = df.isnull().sum().to_dict()
    missing_pct: dict[str, float] = {
        c: round(v / len(df) * 100, 2) for c, v in missing_counts.items() if v > 0
    }

    cardinality: dict[str, int] = {c: df[c].nunique() for c in df.columns}

    skewness: dict[str, float] = {}
    for c in numeric_cols:
        val = df[c].skew()
        # Handle NaN/Inf which are not JSON compliant
        if pd.isna(val) or np.isinf(val):
            skewness[c] = 0.0
        else:
            skewness[c] = round(float(val), 4)

    # Guess target column heuristic (last column that looks like a label)
    has_target_hint = False
    possible_target = df.columns[-1]
    if df[possible_target].nunique() <= 20:
        has_target_hint = True

    class_dist: dict[str, int] = {}
    if has_target_hint:
        class_dist = df[possible_target].value_counts().to_dict()

    profile = {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": df.columns.tolist(),
        "numeric_cols": numeric_cols,
        "categorical_cols": cat_cols,
        "bool_cols": bool_cols,
        "missing_counts": {k: v for k, v in missing_counts.items() if v > 0},
        "missing_pct": missing_pct,
        "total_missing_pct": round(df.isnull().sum().sum() / df.size * 100, 2),
        "cardinality": cardinality,
        "skewness": skewness,
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 3),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "possible_target": possible_target,
        "has_target_hint": has_target_hint,
        "class_distribution": class_dist,
    }

    return sanitize_val(profile)


def describe_dataset(df: pd.DataFrame) -> dict[str, Any]:
    """Extended descriptive statistics for numeric columns."""
    desc = df.describe(include="all").round(4).to_dict()
    return desc
