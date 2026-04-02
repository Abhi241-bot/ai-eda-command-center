"""
iqse.py -- AI Insight Quality Scoring Engine
--------------------------------------------
Uses Gemini to score each EDA tool's insight quality on four dimensions
(correctness, relevance, actionability, coverage) from 1-10,
and computes a weighted overall score.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_SCORING_PROMPT = """
You are an expert data science evaluator.
Below are insights extracted from the EDA tool "{tool_name}" and the true dataset profile.

Dataset Profile:
{dataset_profile}

Tool Insights:
{tool_insights}

Score this tool's insights on the following dimensions (1 = very poor, 10 = excellent):

1. Correctness   -- Are the facts (values, correlations, counts) accurate vs the dataset profile?
2. Relevance     -- Do the insights focus on what matters for downstream ML/analysis?
3. Actionability -- Do the insights lead to clear, specific preprocessing / modelling actions?
4. Coverage      -- Does the tool cover all important aspects (missing values, outliers, distributions, correlations)?

Respond in STRICT JSON with this structure (no extra text):
{{
  "correctness": <int 1-10>,
  "relevance": <int 1-10>,
  "actionability": <int 1-10>,
  "coverage": <int 1-10>,
  "justification": {{
    "correctness": "<one sentence>",
    "relevance": "<one sentence>",
    "actionability": "<one sentence>",
    "coverage": "<one sentence>"
  }}
}}
"""


def score_tool_insights(
    tool_name: str,
    tool_insights: dict[str, Any],
    dataset_profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Score a single tool's insights via Gemini.

    Returns
    -------
    dict with keys: tool, correctness, relevance, actionability, coverage,
                    overall (weighted), justification
    """
    from modules.gemini_client import call_gemini, parse_json_response  # type: ignore
    from config import SCORE_WEIGHTS  # type: ignore

    slim_profile  = {k: v for k, v in dataset_profile.items() if k != "dtypes"}
    slim_insights = {k: v for k, v in tool_insights.items() if k != "tool"}

    prompt = _SCORING_PROMPT.format(
        tool_name=tool_name,
        dataset_profile=json.dumps(slim_profile, indent=2, default=str),
        tool_insights=json.dumps(slim_insights, indent=2, default=str),
    )

    try:
        raw    = call_gemini(prompt, max_tokens=512, temperature=0.1)
        scores = parse_json_response(raw)
    except EnvironmentError as e:
        logger.warning("Gemini not configured for scoring: %s", e)
        return _fallback_score(tool_name, str(e))
    except Exception as e:
        logger.error("IQSE scoring failed for %s: %s", tool_name, e)
        return _fallback_score(tool_name, str(e))

    # Weighted overall
    overall = sum(
        scores.get(dim, 5) * weight
        for dim, weight in SCORE_WEIGHTS.items()
    )
    scores["overall"] = round(overall, 2)
    scores["tool"]    = tool_name
    return scores


def _fallback_score(tool_name: str, reason: str) -> dict[str, Any]:
    return {
        "tool":          tool_name,
        "correctness":   0,
        "relevance":     0,
        "actionability": 0,
        "coverage":      0,
        "overall":       0.0,
        "justification": {k: reason for k in ("correctness", "relevance", "actionability", "coverage")},
        "error":         reason,
    }


def score_all_tools(
    all_tool_insights: dict[str, dict],
    dataset_profile: dict[str, Any],
) -> dict[str, dict]:
    """Score all tools and return a ranked dict (highest overall first)."""
    results: dict[str, dict] = {}
    for tool_name, insights in all_tool_insights.items():
        status = insights.get("status", "")
        if status in ("disabled", "not_installed") or status.startswith("skipped"):
            results[tool_name] = _fallback_score(tool_name, f"Tool {status}")
            continue
        results[tool_name] = score_tool_insights(tool_name, insights, dataset_profile)
    return dict(sorted(results.items(), key=lambda x: x[1].get("overall", 0), reverse=True))


def build_score_table(scores: dict[str, dict]) -> list[dict]:
    """Convert scores dict to a list of row dicts suitable for pd.DataFrame."""
    rows = []
    for tool, s in scores.items():
        rows.append({
            "Tool":          tool.capitalize(),
            "Correctness":   s.get("correctness",   0),
            "Relevance":     s.get("relevance",      0),
            "Actionability": s.get("actionability",  0),
            "Coverage":      s.get("coverage",       0),
            "Overall Score": s.get("overall",        0),
        })
    return sorted(rows, key=lambda x: x["Overall Score"], reverse=True)
