"""
ai_insight_generator.py
────────────────────────
Uses Google Gemini to convert structured statistical summaries into
clear, human-readable analytical narratives.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_NARRATIVE_PROMPT = """
You are a senior data scientist reviewing an automated EDA report.
Below is a JSON-structured statistical profile of a dataset and the
key insights extracted from EDA tools.

Dataset Profile:
{dataset_profile}

Unified EDA Insights:
{unified_insights}

Your task:
1. Write 4-6 paragraphs of clear, concise analytical narrative covering:
   - Dataset overview (shape, types, memory)
   - Missing data observations and implications
   - Notable feature distributions and skewness
   - Significant correlations (including potential multicollinearity risks)
   - Detected outliers and their potential impact
   - Key recommendations for preprocessing and modelling

Rules:
- Be specific - reference actual column names and numbers.
- Avoid jargon - write for a data-literate but non-expert audience.
- Keep each paragraph focused on one theme.
- Output ONLY the narrative text, no JSON or bullet lists.
"""


def generate_narrative(
    dataset_profile: dict[str, Any],
    unified_insights: dict[str, Any],
) -> str:
    """
    Generate a human-readable analytical narrative from dataset stats.

    Parameters
    ----------
    dataset_profile  : Output of data_loader.get_dataset_profile()
    unified_insights : Output of insight_extractor.unify_insights()

    Returns
    -------
    str -- multi-paragraph narrative text
    """
    from modules.gemini_client import call_gemini  # type: ignore

    slim_profile = {k: v for k, v in dataset_profile.items() if k != "dtypes"}
    slim_insights = {
        "consensus": unified_insights.get("consensus", {}),
        "tools_used": list(unified_insights.get("per_tool", {}).keys()),
    }

    prompt = _NARRATIVE_PROMPT.format(
        dataset_profile=json.dumps(slim_profile, indent=2, default=str),
        unified_insights=json.dumps(slim_insights, indent=2, default=str),
    )

    try:
        narrative = call_gemini(prompt, max_tokens=2048, temperature=0.3)
        logger.info("Gemini narrative generated (%d chars)", len(narrative))
        return narrative
    except EnvironmentError as e:
        logger.warning("Gemini not configured: %s", e)
        return f"AI narrative unavailable: {e}"
    except Exception as e:
        logger.error("Gemini call failed: %s", e)
        return f"Narrative generation failed: {e}"


def generate_column_insight(col_name: str, col_stats: dict[str, Any]) -> str:
    """Generate a one-sentence insight for a single column."""
    from modules.gemini_client import call_gemini  # type: ignore
    prompt = (
        f"In one sentence, describe the statistical properties and potential "
        f"data quality issues of the column '{col_name}' with these stats: "
        f"{col_stats}. Be specific and actionable."
    )
    try:
        return call_gemini(prompt, max_tokens=150)
    except Exception as e:
        return f"Column {col_name}: {e}"
