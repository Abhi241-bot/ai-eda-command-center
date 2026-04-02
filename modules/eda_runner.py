"""
eda_runner.py
─────────────
Runs ydata-profiling, Sweetviz, AutoViz, and Lux (with graceful fallback).
Each runner function returns a structured result dict.
"""

from __future__ import annotations

import gc
import logging
import os
import time
import traceback
import warnings
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import psutil

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

# ─── Compatibility Patches ───────────────────────────────────────────────────────
# NumPy 2.0+ removed VisibleDeprecationWarning, which Sweetviz 2.3.1 still expects.
if not hasattr(np, "VisibleDeprecationWarning"):
    # Create a dummy class to prevent AttributeErrors
    class VisibleDeprecationWarning(UserWarning):
        pass
    np.VisibleDeprecationWarning = VisibleDeprecationWarning


# ─── Helpers ─────────────────────────────────────────────────────────────────────

def _memory_mb() -> float:
    proc = psutil.Process(os.getpid())
    return round(proc.memory_info().rss / 1e6, 2)


def _make_result(tool: str, status: str, report_path: str | None,
                 duration: float, mem_start: float, mem_end: float,
                 extra: dict | None = None) -> dict[str, Any]:
    return {
        "tool": tool,
        "status": status,
        "report_path": report_path,
        "duration_sec": round(duration, 3),
        "memory_mb_start": mem_start,
        "memory_mb_end": mem_end,
        "memory_delta_mb": round(mem_end - mem_start, 2),
        **(extra or {}),
    }


# ─── ydata-profiling ─────────────────────────────────────────────────────────────

def run_ydata(df: pd.DataFrame, output_dir: str | Path) -> dict[str, Any]:
    """Generate a ydata-profiling (Pandas Profiling) HTML + JSON report."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "profile_report.html"
    json_path = output_dir / "profile.json"

    mem_start = _memory_mb()
    t0 = time.time()
    try:
        from ydata_profiling import ProfileReport  # type: ignore
        profile = ProfileReport(
            df,
            title="YData Profiling Report",
            explorative=True,
            minimal=False,
            progress_bar=False,
        )
        profile.to_file(html_path)
        # Also export JSON for insight extraction
        profile_json = profile.to_json()
        json_path.write_text(profile_json, encoding="utf-8")
        duration = time.time() - t0
        logger.info("ydata-profiling completed in %.1fs", duration)
        return _make_result(
            "ydata", "success", str(html_path), duration,
            mem_start, _memory_mb(),
            {"json_path": str(json_path)},
        )
    except ImportError:
        return _make_result("ydata", "not_installed", None, time.time() - t0, mem_start, _memory_mb())
    except Exception as e:
        logger.error("ydata-profiling failed: %s", e)
        return _make_result("ydata", f"error: {e}", None, time.time() - t0, mem_start, _memory_mb())
    finally:
        gc.collect()


# ─── Sweetviz ────────────────────────────────────────────────────────────────────

def run_sweetviz(df: pd.DataFrame, output_dir: str | Path) -> dict[str, Any]:
    """Generate a Sweetviz HTML report."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "sweetviz_report.html"

    mem_start = _memory_mb()
    t0 = time.time()
    try:
        import sweetviz as sv  # type: ignore
        report = sv.analyze(df, pairwise_analysis="auto")
        report.show_html(str(html_path), open_browser=False, layout="vertical", scale=1.0)
        duration = time.time() - t0
        logger.info("Sweetviz completed in %.1fs", duration)
        return _make_result("sweetviz", "success", str(html_path), duration, mem_start, _memory_mb())
    except ImportError:
        return _make_result("sweetviz", "not_installed", None, time.time() - t0, mem_start, _memory_mb())
    except Exception as e:
        logger.error("Sweetviz failed: %s", e)
        return _make_result("sweetviz", f"error: {e}", None, time.time() - t0, mem_start, _memory_mb())
    finally:
        gc.collect()


# ─── AutoViz ─────────────────────────────────────────────────────────────────────

def run_autoviz(df: pd.DataFrame, output_dir: str | Path,
                max_rows: int = 2000) -> dict[str, Any]:
    """
    Generate AutoViz charts saved as PNG files.

    Automatically caps the dataset at *max_rows* rows to keep runtime
    under ~10 seconds even on large datasets.
    AutoViz saves charts into a nested subdirectory (e.g. AutoViz_Plots/);
    we search recursively to find all generated PNGs.
    """
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend — must be before pyplot

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Cap rows for speed
    sample = df.head(max_rows) if len(df) > max_rows else df.copy()

    mem_start = _memory_mb()
    t0 = time.time()
    try:
        from autoviz.AutoViz_Class import AutoViz_Class  # type: ignore
        import matplotlib.pyplot as plt
        AV = AutoViz_Class()
        AV.AutoViz(
            filename="",
            sep=",",
            depVar="",
            dfte=sample,
            header=0,
            verbose=0,          # suppress printed output
            lowess=False,
            chart_format="png",
            max_rows_analyzed=max_rows,
            max_cols_analyzed=30,
            save_plot_dir=str(output_dir),
        )
        plt.close("all")
        duration = time.time() - t0

        # AutoViz saves into a nested sub-folder (e.g. AutoViz_Plots/).
        # Search recursively for all PNG files.
        png_files = list(output_dir.rglob("*.png"))
        logger.info("AutoViz completed in %.1fs — %d charts found", duration, len(png_files))
        return _make_result(
            "autoviz", "success", str(output_dir), duration, mem_start, _memory_mb(),
            {"chart_files": [str(p) for p in png_files], "n_charts": len(png_files)},
        )
    except ImportError:
        return _make_result("autoviz", "not_installed", None,
                            time.time() - t0, mem_start, _memory_mb())
    except Exception as e:
        logger.error("AutoViz failed: %s\n%s", e, traceback.format_exc())
        return _make_result("autoviz", f"error: {e}", None,
                            time.time() - t0, mem_start, _memory_mb())
    finally:
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
        gc.collect()


# ─── Lux (headless fallback) ─────────────────────────────────────────────────────

def run_lux(df: pd.DataFrame, output_dir: str | Path) -> dict[str, Any]:
    """
    Attempt to run Lux in headless mode.
    Lux requires a Jupyter kernel; in Streamlit/script context we extract
    metadata from the lux.config and Vis recommendations without rendering.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mem_start = _memory_mb()
    t0 = time.time()
    try:
        import lux  # type: ignore  # noqa: F401
        import lux.core  # noqa: F401
        lux_df = df.copy()
        lux_df._repr_html_()  # triggers Lux recommendation engine
        recs = lux_df.recommendation

        import json
        summaries = []
        for action_type, vis_list in recs.items():
            for vis in vis_list[:3]:  # top 3 per action
                summaries.append({
                    "action": action_type,
                    "title": str(vis.title),
                    "score": getattr(vis, "score", None),
                })
        json_path = output_dir / "lux_recommendations.json"
        json_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
        duration = time.time() - t0
        logger.info("Lux completed in %.1fs", duration)
        return _make_result(
            "lux", "success", str(json_path), duration, mem_start, _memory_mb(),
            {"recommendations": summaries},
        )
    except ImportError:
        logger.warning("Lux not installed — skipping.")
        return _make_result("lux", "not_installed", None, time.time() - t0, mem_start, _memory_mb())
    except Exception as e:
        logger.warning("Lux failed (expected in non-Jupyter env): %s", e)
        return _make_result("lux", f"skipped: {e}", None, time.time() - t0, mem_start, _memory_mb())
    finally:
        gc.collect()


# ─── Dispatcher ──────────────────────────────────────────────────────────────────

TOOL_RUNNERS: dict[str, Callable] = {
    "ydata":    run_ydata,
    "sweetviz": run_sweetviz,
    "autoviz":  run_autoviz,
    "lux":      run_lux,
}


def run_all_tools(
    df: pd.DataFrame,
    reports_base: str | Path,
    enabled_tools: dict[str, bool] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Run all enabled EDA tools and return a dict of results keyed by tool name.

    Parameters
    ----------
    df            : Input DataFrame
    reports_base  : Base directory where per-tool subdirs will be created
    enabled_tools : Override dict; defaults to config.TOOLS_ENABLED
    """
    if enabled_tools is None:
        from config import TOOLS_ENABLED  # type: ignore
        enabled_tools = TOOLS_ENABLED

    results: dict[str, dict[str, Any]] = {}
    for tool_name, enabled in enabled_tools.items():
        if not enabled:
            logger.info("Tool %s is disabled — skipping.", tool_name)
            results[tool_name] = {"tool": tool_name, "status": "disabled"}
            continue
        out_dir = Path(reports_base) / tool_name
        runner = TOOL_RUNNERS.get(tool_name)
        if runner is None:
            logger.warning("No runner found for tool: %s", tool_name)
            continue
        logger.info("Running %s …", tool_name)
        results[tool_name] = runner(df, out_dir)

    return results
