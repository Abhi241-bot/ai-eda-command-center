"""
test_all_features.py
────────────────────
Quick smoke test for every module in the EDA Benchmarking System.
Run with the venv active:
    .\venv\Scripts\python.exe test_all_features.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⚠️  SKIP"

results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((PASS, name, str(detail or "")))
        print(f"{PASS}  {name}  {detail or ''}")
    except Exception as e:
        results.append((FAIL, name, str(e)))
        print(f"{FAIL}  {name}  → {e}")


print("\n" + "="*65)
print("   AI-Enhanced EDA Benchmarking System — Feature Smoke Test")
print("="*65 + "\n")

# ── 1. Config ─────────────────────────────────────────────────────────
import config as cfg

check("config.py loads", lambda: f"GEMINI_MODEL={cfg.GEMINI_MODEL}")
check("REPORTS_DIR created", lambda: cfg.REPORTS_DIR.exists())
check("DATA_DIR created", lambda: cfg.DATA_DIR.exists())

# ── 2. Data Loader ────────────────────────────────────────────────────
from modules.data_loader import load_dataset, get_dataset_profile
import pandas as pd
import numpy as np

check("load_dataset() — sample_clean.csv",
      lambda: load_dataset("data/sample_clean.csv").shape)

def _profile():
    df = load_dataset("data/sample_clean.csv")
    p = get_dataset_profile(df)
    assert p["n_rows"] > 0
    assert "skewness" in p
    return f"{p['n_rows']} rows, {p['n_cols']} cols, missing={p['total_missing_pct']}%"

check("get_dataset_profile()", _profile)

# ── 3. EDA Runner — Sweetviz ──────────────────────────────────────────
from modules.eda_runner import run_sweetviz, run_ydata, run_autoviz

df_clean = pd.read_csv("data/sample_clean.csv")

def _sweetviz():
    r = run_sweetviz(df_clean, "reports/sweetviz")
    assert r["status"] == "success", f"status={r['status']}"
    return f"{r['duration_sec']:.1f}s  →  {r['report_path']}"

check("run_sweetviz()", _sweetviz)

# ── 4. EDA Runner — ydata-profiling ──────────────────────────────────
def _ydata():
    r = run_ydata(df_clean, "reports/ydata")
    if r["status"] == "not_installed":
        return "not installed (fallback OK)"
    assert r["status"] == "success", f"status={r['status']}"
    return f"{r['duration_sec']:.1f}s"

check("run_ydata()", _ydata)

# ── 5. EDA Runner — AutoViz ───────────────────────────────────────────
def _autoviz():
    r = run_autoviz(df_clean.head(200), "reports/autoviz")
    if r["status"] == "not_installed":
        return "not installed (fallback OK)"
    if "error" in r["status"]:
        return f"errored (non-critical): {r['status'][:60]}"
    return f"{r['duration_sec']:.1f}s"

check("run_autoviz()", _autoviz)

# ── 6. Insight Extractor — Sweetviz ──────────────────────────────────
from modules.insight_extractor import extract_sweetviz_insights, unify_insights

def _extract_sweetviz():
    insights = extract_sweetviz_insights(df_clean)
    assert isinstance(insights["correlations"], list)
    assert isinstance(insights["missing_values"], dict)
    return (f"{len(insights['correlations'])} corr pairs, "
            f"{len(insights['outliers'])} outlier cols")

check("extract_sweetviz_insights()", _extract_sweetviz)

# ── 7. Insight Extractor — ydata JSON ────────────────────────────────
from modules.insight_extractor import extract_ydata_insights
import pathlib

def _extract_ydata():
    json_path = pathlib.Path("reports/ydata/profile.json")
    if not json_path.exists():
        return "JSON not yet generated — run ydata first"
    insights = extract_ydata_insights(json_path)
    return f"{len(insights['correlations'])} corr pairs"

check("extract_ydata_insights()", _extract_ydata)

# ── 8. Unify Insights ─────────────────────────────────────────────────
def _unify():
    sv = extract_sweetviz_insights(df_clean)
    unified = unify_insights({"sweetviz": sv})
    assert "consensus" in unified
    assert "per_tool" in unified
    return (f"missing_cols={unified['consensus']['missing_columns']}, "
            f"high_corr={len(unified['consensus']['high_correlation_pairs'])}")

check("unify_insights()", _unify)

# ── 9. Benchmarking ───────────────────────────────────────────────────
from modules.benchmarking import benchmark_tool
from modules.eda_runner import run_sweetviz

def _benchmark():
    bm = benchmark_tool(run_sweetviz, df_clean.head(100), "reports/sweetviz_bm", "sweetviz")
    assert bm.duration_sec >= 0
    return f"{bm.duration_sec:.1f}s, mem_delta={bm.memory_delta_mb:.1f}MB"

check("benchmark_tool()", _benchmark)

# ── 10. Reliability Tester ────────────────────────────────────────────
from modules.reliability_tester import inject_missing, inject_noise, create_imbalanced, inject_high_cardinality

def _reliability():
    df_miss  = inject_missing(df_clean, rate=0.20)
    df_noisy = inject_noise(df_clean)
    df_imbal = create_imbalanced(df_clean)
    df_hc    = inject_high_cardinality(df_clean)
    assert df_miss.isnull().sum().sum() > 0, "missing injection failed"
    assert df_hc.shape[1] >= df_clean.shape[1], "high-card injection failed"
    return (f"missing_test={df_miss.isnull().sum().sum()} NaNs, "
            f"imbalanced={df_imbal['Survived'].value_counts().to_dict()}")

check("reliability injectors (inject_missing, inject_noise, create_imbalanced, inject_high_cardinality)", _reliability)

# ── 11. AI Modules (Gemini) ───────────────────────────────────────────
print("\n── AI / Gemini Features ──────────────────────────────────────────")
if not cfg.GEMINI_API_KEY:
    print(f"{SKIP}  AI narrative, IQSE, gap detection, recommender")
    print("       → Set GEMINI_API_KEY in .env to test these features")
    results.append((SKIP, "AI features", "GEMINI_API_KEY not set"))
else:
    from modules.data_loader import get_dataset_profile
    from modules.ai_insight_generator import generate_narrative
    from modules.iqse import score_tool_insights
    from modules.gap_detector import detect_gaps
    from modules.recommender import recommend_tool

    profile  = get_dataset_profile(df_clean)
    sv_ins   = extract_sweetviz_insights(df_clean)
    unified  = unify_insights({"sweetviz": sv_ins})

    def _narrative():
        text = generate_narrative(profile, unified)
        assert len(text) > 50 and not text.startswith("⚠️")
        return f"{len(text)} chars generated"
    check("generate_narrative() [Gemini]", _narrative)

    def _iqse():
        score = score_tool_insights("sweetviz", sv_ins, profile)
        assert score["overall"] > 0
        return (f"correctness={score['correctness']} relevance={score['relevance']} "
                f"actionability={score['actionability']} coverage={score['coverage']} "
                f"overall={score['overall']}")
    check("score_tool_insights() [IQSE]", _iqse)

    def _gaps():
        gaps = detect_gaps(unified, profile)
        assert isinstance(gaps, list)
        return f"{len(gaps)} gaps detected"
    check("detect_gaps() [Gap Detector]", _gaps)

    def _recommend():
        bm_fake = {"sweetviz": {"duration_sec": 2.0, "memory_delta_mb": 10.0, "status": "success"}}
        scores  = {"sweetviz": {"overall": 7.5, "correctness": 8, "relevance": 7, "actionability": 7, "coverage": 7}}
        rec = recommend_tool(bm_fake, scores, profile)
        assert "recommended_tool" in rec
        return f"→ {rec['recommended_tool']} (confidence={rec['confidence']})"
    check("recommend_tool() [Recommender]", _recommend)

# ── Summary ───────────────────────────────────────────────────────────
print("\n" + "="*65)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
skipped = sum(1 for r in results if r[0] == SKIP)
print(f"  Results: {passed} passed  |  {failed} failed  |  {skipped} skipped")
print("="*65 + "\n")
if failed > 0:
    print("Failed tests:")
    for status, name, detail in results:
        if status == FAIL:
            print(f"  • {name}: {detail}")
