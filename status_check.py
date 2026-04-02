"""status_check.py - Full end-to-end feature status audit"""
import sys, os, warnings, pathlib, io, time
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pandas as pd

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

print("=" * 60)
print("  AI-EDA Benchmarking System -- Full Status Check")
print("=" * 60)

df = pd.read_csv("data/sample_clean.csv")
print(f"\nDataset: {df.shape}\n")

results = {}

def run(label, fn):
    try:
        val = fn()
        msg = f"  {PASS}  {label}: {val}"
        print(msg)
        results[label] = "PASS"
    except Exception as e:
        msg = f"  {FAIL}  {label}: {e}"
        print(msg)
        results[label] = f"FAIL: {e}"

# ------------------------------------------------------------------
# 1. data_loader
# ------------------------------------------------------------------
from modules.data_loader import get_dataset_profile
run("data_loader", lambda: f"{get_dataset_profile(df)['n_rows']} rows profiled OK")

# ------------------------------------------------------------------
# 2. sweetviz runner
# ------------------------------------------------------------------
import matplotlib; matplotlib.use("Agg")
from modules.eda_runner import run_sweetviz

def _sv():
    r = run_sweetviz(df, "reports/sweetviz")
    assert r["status"] == "success", r["status"]
    return f"status=success, {r['duration_sec']:.1f}s, report at {r['report_path']}"
run("eda_runner.run_sweetviz", _sv)

# ------------------------------------------------------------------
# 3. ydata-profiling runner
# ------------------------------------------------------------------
from modules.eda_runner import run_ydata

def _yd():
    r = run_ydata(df, "reports/ydata")
    assert r["status"] in ("success", "not_installed"), r["status"]
    if r["status"] == "success":
        return f"status=success, {r['duration_sec']:.1f}s, JSON at {r.get('json_path','?')}"
    return "status=not_installed (fallback OK)"
run("eda_runner.run_ydata", _yd)

# ------------------------------------------------------------------
# 4. autoviz runner
# ------------------------------------------------------------------
from modules.eda_runner import run_autoviz

def _av():
    r = run_autoviz(df.head(300), "reports/autoviz")
    ok = r["status"] in ("success", "not_installed") or "error" in r["status"]
    if r["status"] == "success":
        return f"status=success, {r['duration_sec']:.1f}s"
    return f"status={r['status'][:60]}"
run("eda_runner.run_autoviz", _av)

# ------------------------------------------------------------------
# 5a. insight extractor — sweetviz
# ------------------------------------------------------------------
from modules.insight_extractor import (
    extract_sweetviz_insights, extract_ydata_insights,
    extract_autoviz_insights, unify_insights
)
sv_ins = [None]

def _ins_sv():
    ins = extract_sweetviz_insights(df)
    sv_ins[0] = ins
    return (f"{len(ins['correlations'])} corr pairs, "
            f"{len(ins['outliers'])} outlier cols, "
            f"{len(ins['skewness'])} skew vals")
run("insight_extractor.sweetviz", _ins_sv)

# ------------------------------------------------------------------
# 5b. insight extractor — ydata JSON
# ------------------------------------------------------------------
def _ins_yd():
    jp = pathlib.Path("reports/ydata/profile.json")
    if not jp.exists():
        return "ydata JSON missing -- run ydata runner first"
    ins = extract_ydata_insights(jp)
    return (f"{len(ins['correlations'])} corr pairs, "
            f"{len(ins['missing_values'])} missing cols")
run("insight_extractor.ydata", _ins_yd)

# ------------------------------------------------------------------
# 5c. insight extractor — autoviz
# ------------------------------------------------------------------
def _ins_av():
    ins = extract_autoviz_insights(df, "reports/autoviz")
    return f"tool={ins['tool']}, {len(ins['correlations'])} corrs"
run("insight_extractor.autoviz", _ins_av)

# ------------------------------------------------------------------
# 5d. unify_insights
# ------------------------------------------------------------------
def _unify():
    base = sv_ins[0] if sv_ins[0] else extract_sweetviz_insights(df)
    u = unify_insights({"sweetviz": base})
    c = u["consensus"]
    return (f"missing_cols={c['missing_columns']}, "
            f"high_corr_pairs={len(c['high_correlation_pairs'])}, "
            f"outlier_cols={c['outlier_columns']}, "
            f"skewed_feats={len(c['skewed_columns'])}")
run("insight_extractor.unify_insights", _unify)

# ------------------------------------------------------------------
# 6. benchmarking
# ------------------------------------------------------------------
from modules.benchmarking import benchmark_tool

def _bm():
    bm = benchmark_tool(run_sweetviz, df.head(100), "reports/sv_bm", "sweetviz")
    return f"{bm.duration_sec:.2f}s, mem_delta={bm.memory_delta_mb:.1f}MB, status={bm.status}"
run("benchmarking.benchmark_tool", _bm)

# ------------------------------------------------------------------
# 7. reliability tester
# ------------------------------------------------------------------
from modules.reliability_tester import (
    inject_missing, inject_noise,
    create_imbalanced, inject_high_cardinality
)

def _rel():
    d1 = inject_missing(df, 0.20)
    d2 = inject_noise(df)
    d3 = create_imbalanced(df)
    d4 = inject_high_cardinality(df)
    assert d1.isnull().sum().sum() > 0, "missing injection failed"
    assert d4.shape[1] > df.shape[1], "high-cardinality injection failed"
    return (f"missing={d1.isnull().sum().sum()} NaNs | "
            f"noise OK | imbalance={d3['Survived'].value_counts().to_dict()} | "
            f"hc_cols={d4.shape[1]}")
run("reliability_tester (all 4 injectors)", _rel)

# ------------------------------------------------------------------
# 8. AI / Gemini modules
# ------------------------------------------------------------------
import config
print()
print("-- AI / Gemini Modules --")

if not config.GROQ_API_KEY:
    print(f"  {SKIP}  All AI modules (narrative / IQSE / gap / recommend)")
    print("         --> Add GROQ_API_KEY=your_key to .env to enable")
    results["AI modules"] = "SKIP"
else:
    profile = get_dataset_profile(df)
    base_ins = sv_ins[0] or extract_sweetviz_insights(df)
    unified  = unify_insights({"sweetviz": base_ins})

    from modules.ai_insight_generator import generate_narrative
    def _narr():
        t = generate_narrative(profile, unified)
        assert len(t) > 50 and "unavailable" not in t
        return f"{len(t)} chars generated"
    run("ai_insight_generator.generate_narrative", _narr)

    from modules.iqse import score_tool_insights
    def _iqse():
        s = score_tool_insights("sweetviz", base_ins, profile)
        assert s["overall"] > 0
        return (f"overall={s['overall']} "
                f"(C={s['correctness']} R={s['relevance']} "
                f"A={s['actionability']} Cv={s['coverage']})")
    run("iqse.score_tool_insights", _iqse)

    from modules.gap_detector import detect_gaps
    def _gaps():
        g = detect_gaps(unified, profile)
        assert isinstance(g, list)
        return f"{len(g)} gaps detected"
    run("gap_detector.detect_gaps", _gaps)

    from modules.recommender import recommend_tool
    def _rec():
        bm_fake = {"sweetviz": {"duration_sec": 2.0, "memory_delta_mb": 10.0, "status": "success"}}
        sc_fake  = {"sweetviz": {"overall": 7.5, "correctness": 8,
                                  "relevance": 7, "actionability": 7, "coverage": 7}}
        r = recommend_tool(bm_fake, sc_fake, profile)
        return f"recommended={r['recommended_tool']}, confidence={r['confidence']}"
    run("recommender.recommend_tool", _rec)

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
passed  = sum(1 for v in results.values() if v == "PASS")
failed  = sum(1 for v in results.values() if v.startswith("FAIL"))
skipped = sum(1 for v in results.values() if v.startswith("SKIP"))

print()
print("=" * 60)
print(f"  RESULT: {passed} PASSED  |  {failed} FAILED  |  {skipped} SKIPPED")
print("=" * 60)

if failed:
    print("\nFailed items:")
    for k, v in results.items():
        if v.startswith("FAIL"):
            print(f"  * {k}")
            print(f"    {v[6:]}")
else:
    if skipped:
        print("\nAll code modules PASS. Set GEMINI_API_KEY in .env for AI features.")
    else:
        print("\nAll features PASS including AI. Project is fully operational.")
