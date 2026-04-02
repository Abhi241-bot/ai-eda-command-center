"""
insight_extractor.py
────────────────────
Parses each EDA tool's output (HTML, JSON, charts) into a unified
canonical insight schema (dict/JSON-serialisable).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─── Canonical Schema ────────────────────────────────────────────────────────────

def _empty_insights(tool: str) -> dict[str, Any]:
    return {
        "tool": tool,
        "missing_values": {},
        "correlations": [],
        "distributions": {},
        "outliers": [],
        "skewness": {},
        "cardinality": {},
        "high_correlation_pairs": [],
        "warnings": [],
        "summary_stats": {},
    }


# ─── ydata-profiling ─────────────────────────────────────────────────────────────

def extract_ydata_insights(json_path: str | Path) -> dict[str, Any]:
    """Parse the exported ydata profile JSON into canonical insight schema."""
    out = _empty_insights("ydata")
    try:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))

        variables: dict = data.get("variables", {})
        for col, info in variables.items():
            # Missing values
            n_missing = info.get("n_missing", 0)
            if n_missing > 0:
                out["missing_values"][col] = {
                    "count": n_missing,
                    "pct": round(info.get("p_missing", 0) * 100, 2),
                }
            # Skewness
            if "skewness" in info:
                out["skewness"][col] = round(info["skewness"], 4)
            # Distributions (mean, std, min, max)
            if info.get("type") in ("Numeric", "Real", "Integer"):
                out["distributions"][col] = {
                    "mean": info.get("mean"),
                    "std": info.get("std"),
                    "min": info.get("min"),
                    "max": info.get("max"),
                    "median": info.get("median"),
                    "kurtosis": info.get("kurtosis"),
                }
            # Cardinality
            out["cardinality"][col] = info.get("n_distinct", info.get("n_unique", None))
            # Warnings from ydata
            for alert in info.get("alerts", []):
                out["warnings"].append(f"{col}: {alert}")

        # Correlations from correlation matrix
        correlations_block = data.get("correlations", {})
        pearson = correlations_block.get("pearson", {})
        for col_a, row in pearson.items():
            for col_b, corr_val in row.items():
                if col_a >= col_b:
                    continue
                try:
                    val = float(corr_val)
                    pair = {"feature_a": col_a, "feature_b": col_b, "pearson": round(val, 4)}
                    out["correlations"].append(pair)
                    if abs(val) >= 0.7:
                        out["high_correlation_pairs"].append(pair)
                except (TypeError, ValueError):
                    pass

        # Global alerts / warnings
        for alert in data.get("alerts", []):
            msg = alert if isinstance(alert, str) else str(alert)
            if msg not in out["warnings"]:
                out["warnings"].append(msg)

    except Exception as e:
        logger.error("ydata insight extraction failed: %s", e)
        out["warnings"].append(f"Extraction error: {e}")
    return out


# ─── Sweetviz ────────────────────────────────────────────────────────────────────

def extract_sweetviz_insights(df: pd.DataFrame) -> dict[str, Any]:
    """
    Derive Sweetviz-style insights directly from the DataFrame
    (Sweetviz HTML is not easily parseable, so we recompute key statistics).
    """
    out = _empty_insights("sweetviz")
    try:
        numeric_df = df.select_dtypes(include=[np.number])

        # Missing values
        for col in df.columns:
            n = df[col].isnull().sum()
            if n > 0:
                out["missing_values"][col] = {"count": int(n), "pct": round(n / len(df) * 100, 2)}

        # Distributions + skewness
        for col in numeric_df.columns:
            desc = numeric_df[col].describe()
            out["distributions"][col] = {
                "mean": round(float(desc["mean"]), 4),
                "std": round(float(desc["std"]), 4),
                "min": round(float(desc["min"]), 4),
                "max": round(float(desc["max"]), 4),
                "median": round(float(numeric_df[col].median()), 4),
            }
            out["skewness"][col] = round(float(numeric_df[col].skew()), 4)

        # Cardinality
        for col in df.columns:
            out["cardinality"][col] = int(df[col].nunique())

        # Correlations (Pearson)
        corr_matrix = numeric_df.corr()
        cols = corr_matrix.columns.tolist()
        for i, col_a in enumerate(cols):
            for j, col_b in enumerate(cols):
                if j <= i:
                    continue
                val = corr_matrix.loc[col_a, col_b]
                if pd.isna(val):
                    continue
                pair = {"feature_a": col_a, "feature_b": col_b, "pearson": round(float(val), 4)}
                out["correlations"].append(pair)
                if abs(val) >= 0.7:
                    out["high_correlation_pairs"].append(pair)

        # Outlier detection (IQR)
        for col in numeric_df.columns:
            q1, q3 = numeric_df[col].quantile(0.25), numeric_df[col].quantile(0.75)
            iqr = q3 - q1
            n_out = int(((numeric_df[col] < q1 - 1.5 * iqr) | (numeric_df[col] > q3 + 1.5 * iqr)).sum())
            if n_out > 0:
                out["outliers"].append({"column": col, "n_outliers": n_out,
                                        "pct": round(n_out / len(df) * 100, 2)})

    except Exception as e:
        logger.error("Sweetviz insight extraction failed: %s", e)
        out["warnings"].append(f"Extraction error: {e}")
    return out


# ─── AutoViz ─────────────────────────────────────────────────────────────────────

def extract_autoviz_insights(df: pd.DataFrame, output_dir: str | Path) -> dict[str, Any]:
    """
    AutoViz saves PNG charts; we extract insights from the DataFrame directly
    and note which charts were generated.
    """
    out = _empty_insights("autoviz")
    output_dir = Path(output_dir)
    try:
        # Reuse same logic as sweetviz (statistical extraction)
        sv_insights = extract_sweetviz_insights(df)
        out.update({k: v for k, v in sv_insights.items() if k != "tool"})
        out["tool"] = "autoviz"

        # Note chart files
        charts = list(output_dir.glob("*.png"))
        out["chart_files"] = [p.name for p in charts]
        out["warnings"].append(f"{len(charts)} chart(s) generated by AutoViz.")
    except Exception as e:
        logger.error("AutoViz insight extraction failed: %s", e)
        out["warnings"].append(f"Extraction error: {e}")
    return out


# ─── Lux ─────────────────────────────────────────────────────────────────────────

def extract_lux_insights(json_path: str | Path | None) -> dict[str, Any]:
    """Parse Lux recommendation JSON if available."""
    out = _empty_insights("lux")
    if json_path is None or not Path(str(json_path)).exists():
        out["warnings"].append("Lux output not available.")
        return out
    try:
        recs = json.loads(Path(json_path).read_text(encoding="utf-8"))
        out["lux_recommendations"] = recs
        out["warnings"].append(f"{len(recs)} Lux recommendations extracted.")
    except Exception as e:
        out["warnings"].append(f"Lux extraction error: {e}")
    return out


# ─── Unifier ─────────────────────────────────────────────────────────────────────

def unify_insights(tool_insights: dict[str, dict]) -> dict[str, Any]:
    """
    Merge all tool insight dicts into a single canonical representation
    with per-tool breakdowns and a consensus summary.
    """
    unified: dict[str, Any] = {
        "per_tool": tool_insights,
        "consensus": {
            "missing_columns": set(),
            "high_correlation_pairs": [],
            "outlier_columns": set(),
            "skewed_columns": [],
            "warnings": [],
        },
    }

    seen_corr_pairs: set[tuple] = set()
    for tool, insights in tool_insights.items():
        if not isinstance(insights, dict):
            continue

        # Missing columns
        for col in insights.get("missing_values", {}):
            unified["consensus"]["missing_columns"].add(col)

        # High correlations
        for pair in insights.get("high_correlation_pairs", []):
            key = tuple(sorted([pair["feature_a"], pair["feature_b"]]))
            if key not in seen_corr_pairs:
                seen_corr_pairs.add(key)
                unified["consensus"]["high_correlation_pairs"].append(pair)

        # Outlier columns
        for entry in insights.get("outliers", []):
            unified["consensus"]["outlier_columns"].add(entry["column"])

        # Highly skewed columns (|skew| > 1)
        for col, skew in insights.get("skewness", {}).items():
            if abs(skew) > 1.0:
                unified["consensus"]["skewed_columns"].append({"column": col, "skewness": skew})

    # Serialise sets → sorted lists
    unified["consensus"]["missing_columns"] = sorted(unified["consensus"]["missing_columns"])
    unified["consensus"]["outlier_columns"] = sorted(unified["consensus"]["outlier_columns"])

    return unified
