"""
recommender.py
--------------
Dataset-aware EDA tool recommendation engine.
Combines IQSE scores, benchmark performance, and dataset characteristics
to recommend the best tool via Gemini.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_RECOMMEND_PROMPT = """
You are a senior data scientist choosing the best automated EDA tool for a project.

Dataset Characteristics:
{dataset_profile}

Tool Benchmark Results (runtime, memory):
{benchmark_results}

Tool Insight Quality Scores (1-10 per dimension, overall weighted):
{iqse_scores}

Available tools: {tool_list}

Based on all the above, recommend ONE best tool for this specific dataset.
Consider:
- If dataset is small (<10k rows), quality matters more than speed.
- If large (>100k rows), favour tools with lower runtime/memory.
- Prefer tools with higher overall IQSE score.
- Prefer tools that successfully ran without errors.

Respond in STRICT JSON only (no extra text):
{{
  "recommended_tool": "<tool_name>",
  "confidence": "<High|Medium|Low>",
  "overall_winner_score": <float 0-10>,
  "explanation": "<2-3 sentence explanation referencing specific scores and dataset properties>",
  "runner_up": "<second best tool or null>",
  "avoid": "<tool to avoid and why (one sentence)>"
}}
"""


def recommend_tool(
    benchmark_results: dict[str, Any],
    iqse_scores: dict[str, Any],
    dataset_profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Recommend the best EDA tool for the dataset.

    Returns
    -------
    dict with keys: recommended_tool, confidence, explanation, runner_up, avoid
    """
    from modules.gemini_client import call_gemini, parse_json_response  # type: ignore

    slim_benchmarks = {
        t: {
            "duration_sec":    v.get("duration_sec")    if isinstance(v, dict) else getattr(v, "duration_sec",    0),
            "memory_delta_mb": v.get("memory_delta_mb") if isinstance(v, dict) else getattr(v, "memory_delta_mb", 0),
            "status":          v.get("status")          if isinstance(v, dict) else getattr(v, "status",          "?"),
        }
        for t, v in benchmark_results.items()
    }
    slim_scores = {
        t: {k: v for k, v in s.items()
            if k in ("overall", "correctness", "relevance", "actionability", "coverage")}
        for t, s in iqse_scores.items()
    }
    slim_profile = {
        k: v for k, v in dataset_profile.items()
        if k in ("n_rows", "n_cols", "numeric_cols", "categorical_cols",
                  "total_missing_pct", "possible_target", "has_target_hint")
    }

    prompt = _RECOMMEND_PROMPT.format(
        dataset_profile=json.dumps(slim_profile, indent=2, default=str),
        benchmark_results=json.dumps(slim_benchmarks, indent=2, default=str),
        iqse_scores=json.dumps(slim_scores, indent=2, default=str),
        tool_list=list(benchmark_results.keys()),
    )

    try:
        raw = call_gemini(prompt, max_tokens=512, temperature=0.1)
        return parse_json_response(raw)
    except EnvironmentError as e:
        logger.warning("Gemini not configured: %s", e)
        return _heuristic_recommend(iqse_scores, str(e))
    except Exception as e:
        logger.error("Recommendation failed: %s", e)
        return _heuristic_recommend(iqse_scores, str(e))


def _heuristic_recommend(iqse_scores: dict[str, Any], reason: str) -> dict[str, Any]:
    """Fallback: pick the tool with the highest IQSE overall score."""
    best = max(iqse_scores, key=lambda t: iqse_scores[t].get("overall", 0), default="ydata")
    return {
        "recommended_tool":   best,
        "confidence":         "Low",
        "overall_winner_score": iqse_scores.get(best, {}).get("overall", 0),
        "explanation": (
            f"Heuristic recommendation (Gemini unavailable: {reason}). "
            f"{best.capitalize()} had the highest IQSE score."
        ),
        "runner_up": None,
        "avoid":     None,
    }
