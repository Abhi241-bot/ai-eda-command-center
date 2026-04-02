"""
modules/gemini_client.py  (now uses Groq backend)
──────────────────────────────────────────────────
Shared LLM client used by all AI modules.
Switched from Google Gemini → Groq for faster, rate-limit-free inference.

Supported Groq models (fast, free tier):
  - llama-3.3-70b-versatile   (default, best quality)
  - llama-3.1-8b-instant      (fastest)
  - mixtral-8x7b-32768        (large context)
"""

from __future__ import annotations

import re
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def call_gemini(prompt: str, max_tokens: int = 2048, temperature: float = 0.3) -> str:
    """
    Send *prompt* to the configured LLM and return the text response.
    Function name kept as call_gemini for backward compatibility,
    but internally uses Groq.
    """
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("Run: pip install groq")

    from dotenv import load_dotenv
    load_dotenv()

    import os
    api_key = os.getenv("GROQ_API_KEY", "")
    model   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file."
        )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def parse_json_response(text: str) -> Any:
    """Strip markdown fences and parse JSON."""
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    return json.loads(text)
