"""
gap_detector.py
---------------
Uses Gemini to detect important analytical insights that NONE of the EDA
tools identified, helping users understand blind spots of automated EDA.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_GAP_PROMPT = """
You are a meticulous senior data scientist auditing a set of automated EDA reports.

Dataset Profile:
{dataset_profile}

Combined insights from ALL EDA tools:
{unified_insights}

Your task: Identify up to 8 important analytical insights that NONE of the EDA tools detected.

Focus on:
- Multicollinearity (highly correlated feature pairs causing redundancy)
- Class imbalance impact
- Hidden data leakage risks (e.g., an ID column correlated with target)
- Temporal patterns (if date columns exist)
- Interaction effects between features
- Data drift risks (extreme outliers in specific ranges)
- Features with near-zero variance (no predictive value)

For each gap, write ONE sentence:
  1. What was missed  2. Why it matters  3. What action to take

Respond as a JSON array (STRICT JSON, no extra text):
[
  {{"gap": "Description of what was missed, why it matters, and what to do"}},
  ...
]
If no meaningful gaps found, return: []
"""


def detect_gaps(
    unified_insights: dict[str, Any],
    dataset_profile: dict[str, Any],
) -> list[str]:
    """
    Detect analytical gaps missed by all EDA tools combined.

    Returns
    -------
    list[str] -- each item is a gap description
    """
    from modules.gemini_client import call_gemini, parse_json_response  # type: ignore

    slim_profile  = {k: v for k, v in dataset_profile.items() if k != "dtypes"}
    slim_insights = unified_insights.get("consensus", {})

    prompt = _GAP_PROMPT.format(
        dataset_profile=json.dumps(slim_profile, indent=2, default=str),
        unified_insights=json.dumps(slim_insights, indent=2, default=str),
    )

    try:
        raw       = call_gemini(prompt, max_tokens=1024, temperature=0.2)
        gaps_data = parse_json_response(raw)
        gaps = [item.get("gap", str(item)) for item in gaps_data if item]
        logger.info("Gap detector found %d gaps.", len(gaps))
        return gaps
    except EnvironmentError as e:
        logger.warning("Gemini not configured for gap detection: %s", e)
        return [f"Gap detection unavailable: {e}"]
    except Exception as e:
        logger.error("Gap detection failed: %s", e)
        return [f"Gap detection error: {e}"]
