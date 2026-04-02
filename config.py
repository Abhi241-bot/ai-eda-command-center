"""
Global configuration for the AI-Enhanced Automated EDA Benchmarking System.
All settings can be overridden via environment variables or a .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ─── Directory Layout ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

for tool in ["ydata", "sweetviz", "autoviz", "lux"]:
    (REPORTS_DIR / tool).mkdir(parents=True, exist_ok=True)

# ─── Groq API (LLM backend) ─────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Legacy Gemini settings (kept for reference; not used when GROQ_API_KEY is set)
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

# ─── EDA Tool Toggles ────────────────────────────────────────────────────────────
TOOLS_ENABLED = {
    "ydata":    True,
    "sweetviz": True,
    "autoviz":  True,
    "lux":      False,   # Set True if lux-api is installed in your environment
}

# ─── Benchmarking ────────────────────────────────────────────────────────────────
SCALABILITY_FRACTIONS = [0.1, 0.25, 0.5, 1.0]   # Fractions of dataset to test
BENCHMARK_TIMEOUT_SEC = 300                        # Cap per-tool run at 5 minutes

# ─── IQSE Scoring ────────────────────────────────────────────────────────────────
SCORE_DIMENSIONS = ["correctness", "relevance", "actionability", "coverage"]
SCORE_WEIGHTS = {
    "correctness":   0.30,
    "relevance":     0.25,
    "actionability": 0.25,
    "coverage":      0.20,
}

# ─── Reliability Testing ─────────────────────────────────────────────────────────
RELIABILITY_SCENARIOS = {
    "missing_low":       0.10,   # 10% missing
    "missing_high":      0.40,   # 40% missing
    "noisy_data":        True,
    "imbalanced":        True,
    "high_cardinality":  True,
}

# ─── Streamlit UI ────────────────────────────────────────────────────────────────
APP_TITLE = "AI-Enhanced EDA Benchmarking System"
APP_ICON = "🔬"

# ─── Logging ─────────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
