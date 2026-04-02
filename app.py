"""
app.py — Streamlit Dashboard
─────────────────────────────
AI-Enhanced Automated EDA Benchmarking and Insight Evaluation System.
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402

# ─── Page config (must be first Streamlit call) ──────────────────────────────────
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Logging ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app")


# ─── Custom CSS ──────────────────────────────────────────────────────────────────
def _inject_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid #0f3460;
    }
    [data-testid="stSidebar"] * { color: #e8e8e8 !important; }

    /* Cards */
    .metric-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(99,102,241,0.25);
    }

    /* Recommendation card */
    .rec-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        color: white;
        box-shadow: 0 8px 32px rgba(102,126,234,0.4);
    }

    /* Gap card */
    .gap-card {
        background: rgba(239,68,68,0.12);
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        color: #fca5a5;
    }

    /* Section headers */
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #a78bfa;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid rgba(167,139,250,0.25);
        padding-bottom: 0.25rem;
    }

    /* Score badges */
    .score-high { color: #34d399; font-weight: 600; }
    .score-mid  { color: #fbbf24; font-weight: 600; }
    .score-low  { color: #f87171; font-weight: 600; }

    /* Dataframe */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* Tabs */
    [data-testid="stTab"] { font-size: 0.9rem; }

    /* Progress bar colour */
    .stProgress > div > div > div { background: linear-gradient(90deg, #667eea, #764ba2) !important; }
    </style>
    """, unsafe_allow_html=True)


# ─── Session State Helpers ────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "df": None,
        "dataset_profile": None,
        "eda_results": {},
        "tool_insights": {},
        "unified_insights": None,
        "iqse_scores": {},
        "benchmark_results": {},
        "gaps": [],
        "narrative": "",
        "recommendation": {},
        "reliability_results": {},
        "file_name": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─── Sidebar ─────────────────────────────────────────────────────────────────────
def _sidebar() -> dict[str, bool]:
    with st.sidebar:
        st.markdown("## 🔬 EDA Benchmark")
        st.markdown("---")

        st.markdown("### 🛠 Select EDA Tools")
        enabled_tools = {}
        for tool, default in config.TOOLS_ENABLED.items():
            label = {
                "ydata":    "📊 ydata-profiling",
                "sweetviz": "🍭 Sweetviz",
                "autoviz":  "🤖 AutoViz",
                "lux":      "✨ Lux (experimental)",
            }.get(tool, tool)
            enabled_tools[tool] = st.checkbox(label, value=default, key=f"tool_{tool}")

        st.markdown("### ⚙️ Settings")
        # API Key is now hardcoded in .env for a seamless experience
        
        run_benchmark = st.checkbox("Run Benchmarks", value=True)
        run_reliability = st.checkbox("Run Reliability Tests", value=False)

        st.markdown("---")
        st.markdown(
            "<small style='color:#888'>AI-Enhanced EDA Benchmarking<br>Powered by Groq + Streamlit</small>",
            unsafe_allow_html=True,
        )
    return enabled_tools, run_benchmark, run_reliability


# ─── Tab 1: Upload & Preview ──────────────────────────────────────────────────────
def tab_upload() -> None:
    st.markdown('<p class="section-header">📁 Upload Dataset</p>', unsafe_allow_html=True)

    col_up, col_sample = st.columns([2, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Upload a CSV file", type=["csv", "tsv"],
            help="Accepts CSV or TSV files up to 200 MB",
        )
    with col_sample:
        st.markdown("#### 📂 Or use a sample:")
        sample_files = list((ROOT / "data").glob("*.csv"))
        sample_names = [f.name for f in sample_files]
        selected_sample = st.selectbox("Sample datasets", ["— None —"] + sample_names)

    # Load dataset
    df = None
    fname = ""
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        fname = uploaded.name
    elif selected_sample != "— None —":
        df = pd.read_csv(ROOT / "data" / selected_sample)
        fname = selected_sample

    if df is not None:
        st.session_state["df"] = df
        st.session_state["file_name"] = fname
        from modules.data_loader import get_dataset_profile
        st.session_state["dataset_profile"] = get_dataset_profile(df)

    df = st.session_state.get("df")
    if df is None:
        st.info("👆 Upload a CSV or select a sample dataset to begin.")
        return

    profile = st.session_state["dataset_profile"]
    st.success(f"✅ **{st.session_state['file_name']}** loaded — {profile['n_rows']:,} rows × {profile['n_cols']} columns")

    # Quick metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, "Rows", f"{profile['n_rows']:,}", ""),
        (c2, "Columns", str(profile['n_cols']), ""),
        (c3, "Numeric", str(len(profile['numeric_cols'])), ""),
        (c4, "Categorical", str(len(profile['categorical_cols'])), ""),
        (c5, "Missing %", f"{profile['total_missing_pct']}%",
         "delta_color" if profile['total_missing_pct'] < 5 else "off"),
    ]
    for col, label, val, _ in metrics:
        with col:
            st.metric(label, val)

    st.markdown("---")
    # Preview
    t1, t2, t3 = st.tabs(["📄 Data Preview", "📈 Skewness", "❓ Missing Values"])
    with t1:
        st.dataframe(df.head(50), use_container_width=True)
    with t2:
        skew_data = profile.get("skewness", {})
        if skew_data:
            skew_df = pd.DataFrame(list(skew_data.items()), columns=["Feature", "Skewness"])
            skew_df = skew_df.sort_values("Skewness", key=abs, ascending=False)
            fig = px.bar(
                skew_df, x="Feature", y="Skewness",
                color="Skewness", color_continuous_scale="RdYlGn_r",
                title="Feature Skewness",
                template="plotly_dark",
            )
            fig.update_layout(height=350, margin=dict(t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric columns for skewness analysis.")
    with t3:
        miss = profile.get("missing_pct", {})
        if miss:
            miss_df = pd.DataFrame(list(miss.items()), columns=["Feature", "Missing %"])
            miss_df = miss_df.sort_values("Missing %", ascending=True)
            fig = px.bar(
                miss_df, x="Missing %", y="Feature",
                orientation="h", title="Missing Value % per Feature",
                color="Missing %", color_continuous_scale="Reds",
                template="plotly_dark",
            )
            fig.update_layout(height=max(200, len(miss_df) * 30), margin=dict(t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("🎉 No missing values detected!")


# ─── Tab 2: Run EDA Tools ─────────────────────────────────────────────────────────
def tab_run_eda(enabled_tools: dict[str, bool]) -> None:
    st.markdown('<p class="section-header">🔬 Run Automated EDA Tools</p>', unsafe_allow_html=True)

    df = st.session_state.get("df")
    if df is None:
        st.warning("Please upload a dataset first (Tab 1).")
        return

    active_tools = [t for t, en in enabled_tools.items() if en]
    if not active_tools:
        st.warning("Enable at least one EDA tool in the sidebar.")
        return

    st.info(f"Ready to run: **{', '.join(t.capitalize() for t in active_tools)}** on {len(df):,} rows.")

    if st.button("▶ Run EDA Tools", type="primary", use_container_width=True):
        from modules.eda_runner import TOOL_RUNNERS
        from modules.insight_extractor import (
            extract_ydata_insights, extract_sweetviz_insights,
            extract_autoviz_insights, extract_lux_insights, unify_insights,
        )

        results: dict = {}
        tool_insights: dict = {}
        progress = st.progress(0.0, text="Starting …")
        status_cols = st.columns(len(active_tools))

        for i, tool in enumerate(active_tools):
            progress.progress((i) / len(active_tools), text=f"Running {tool} …")
            with status_cols[i]:
                with st.spinner(f"{tool} …"):
                    runner = TOOL_RUNNERS[tool]
                    out_dir = config.REPORTS_DIR / tool
                    t0 = time.perf_counter()
                    try:
                        result = runner(df, out_dir)
                    except Exception as e:
                        result = {"tool": tool, "status": f"error: {e}"}
                    results[tool] = result
                    elapsed = time.perf_counter() - t0

                status = result.get("status", "?")
                icon = "✅" if status == "success" else "⚠️"
                st.markdown(f"{icon} **{tool.capitalize()}**  \n`{elapsed:.1f}s`")

        progress.progress(1.0, text="EDA runs complete!")

        # Extract insights
        profile = st.session_state["dataset_profile"]
        with st.spinner("Extracting insights from reports …"):
            # ydata
            ydata_r = results.get("ydata", {})
            if ydata_r.get("json_path"):
                tool_insights["ydata"] = extract_ydata_insights(ydata_r["json_path"])
            elif ydata_r.get("status") == "success":
                tool_insights["ydata"] = extract_sweetviz_insights(df)  # fallback

            # sweetviz
            if "sweetviz" in results and results["sweetviz"].get("status") == "success":
                tool_insights["sweetviz"] = extract_sweetviz_insights(df)

            # autoviz
            if "autoviz" in results and results["autoviz"].get("status") == "success":
                autoviz_dir = config.REPORTS_DIR / "autoviz"
                tool_insights["autoviz"] = extract_autoviz_insights(df, autoviz_dir)

            # lux
            if "lux" in results:
                lux_r = results["lux"]
                tool_insights["lux"] = extract_lux_insights(lux_r.get("report_path"))

        unified = unify_insights(tool_insights)
        st.session_state["eda_results"] = results
        st.session_state["tool_insights"] = tool_insights
        st.session_state["unified_insights"] = unified

        st.success("✅ EDA complete! Proceed to the **View Reports** or **AI Analysis** tabs.")

        # Quick results table
        rows = []
        for t, r in results.items():
            rows.append({
                "Tool": t.capitalize(),
                "Status": r.get("status", "?"),
                "Duration (s)": r.get("duration_sec", "—"),
                "Memory Δ (MB)": r.get("memory_delta_mb", "—"),
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─── Tab 3: View Reports ──────────────────────────────────────────────────────────
def tab_reports() -> None:
    st.markdown('<p class="section-header">📊 EDA Reports</p>', unsafe_allow_html=True)

    eda_results = st.session_state.get("eda_results", {})
    if not eda_results:
        st.info("Run EDA tools first (Tab 2).")
        return

    success_tools = {t: r for t, r in eda_results.items() if r.get("status") == "success"}
    if not success_tools:
        st.warning("No tools ran successfully.")
        return

    selected = st.radio(
        "Select tool report to view:",
        list(success_tools.keys()),
        format_func=str.capitalize,
        horizontal=True,
    )
    st.markdown("---")
    r = success_tools[selected]
    report_path = r.get("report_path", "")

    if report_path and report_path.endswith(".html") and Path(report_path).exists():
        with open(report_path, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()
        st.download_button(
            f"⬇ Download {selected.capitalize()} Report",
            data=html_content,
            file_name=Path(report_path).name,
            mime="text/html",
        )
        with st.expander("🖥 Preview Report (embedded)", expanded=True):
            st.components.v1.html(html_content, height=900, scrolling=True)

    elif selected == "autoviz":
        chart_files = r.get("chart_files", [])
        if chart_files:
            st.write(f"Found {len(chart_files)} charts:")
            cols = st.columns(min(3, len(chart_files)))
            for i, cf in enumerate(chart_files):
                chart_path = Path(cf)
                if chart_path.exists():
                    with cols[i % 3]:
                        st.image(str(chart_path), caption=chart_path.stem)
        else:
            st.info("AutoViz charts not found. Check the reports/autoviz directory.")

    elif selected == "lux":
        recs = r.get("recommendations", [])
        if recs:
            st.json(recs)
        else:
            st.info("Lux ran in limited mode. Recommendations not available in Streamlit context.")
    else:
        st.info(f"Report at: `{report_path}`")

    # Extracted insights
    tool_insights = st.session_state.get("tool_insights", {})
    if selected in tool_insights:
        with st.expander("🔍 Extracted Insights (JSON)", expanded=False):
            st.json(tool_insights[selected])


# ─── Tab 4: AI Analysis ───────────────────────────────────────────────────────────
def tab_ai_analysis() -> None:
    st.markdown('<p class="section-header">🤖 AI Analysis</p>', unsafe_allow_html=True)

    eda_results = st.session_state.get("eda_results", {})
    if not eda_results:
        st.info("Run EDA tools first (Tab 2).")
        return

    profile = st.session_state.get("dataset_profile", {})
    unified = st.session_state.get("unified_insights")

    col_narr, col_gap = st.columns(2)

    # ── Narrative
    with col_narr:
        st.subheader("📝 AI Narrative Summary")
        if st.button("Generate Narrative", type="primary"):
            if not os.getenv("GROQ_API_KEY"):
                st.error("Set your Groq API key in the sidebar first.")
            else:
                with st.spinner("Asking AI to analyse your dataset …"):
                    from modules.ai_insight_generator import generate_narrative
                    narrative = generate_narrative(profile, unified)
                    st.session_state["narrative"] = narrative

        narrative = st.session_state.get("narrative", "")
        if narrative:
            if narrative.startswith("⚠️"):
                st.error(narrative)
            else:
                st.markdown(narrative)
        else:
            st.caption("Click 'Generate Narrative' to produce an AI-powered analytical summary.")

    # ── Gap Detection
    with col_gap:
        st.subheader("🕵️ AI Gap Detection")
        if st.button("Detect Insight Gaps", type="primary"):
            if not os.getenv("GROQ_API_KEY"):
                st.error("Set your Groq API key in the sidebar first.")
            else:
                with st.spinner("Scanning for missed insights …"):
                    from modules.gap_detector import detect_gaps
                    gaps = detect_gaps(unified, profile)
                    st.session_state["gaps"] = gaps

        gaps = st.session_state.get("gaps", [])
        if gaps:
            if all(g.startswith("⚠️") for g in gaps):
                st.error(gaps[0])
            else:
                for g in gaps:
                    st.markdown(
                        f'<div class="gap-card">⚠️ {g}</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("Click 'Detect Insight Gaps' to find what the EDA tools missed.")

    # ── Consensus summary
    if unified:
        st.markdown("---")
        st.subheader("🤝 Cross-Tool Consensus")
        c = unified.get("consensus", {})
        cols = st.columns(4)
        with cols[0]:
            missing = c.get("missing_columns", [])
            st.metric("Columns with Missing Data", len(missing))
            if missing:
                st.caption(", ".join(missing[:5]))
        with cols[1]:
            high_corr = c.get("high_correlation_pairs", [])
            st.metric("High Correlations (≥0.7)", len(high_corr))
            if high_corr:
                pair = high_corr[0]
                st.caption(f"{pair['feature_a']} ↔ {pair['feature_b']}: {pair['pearson']}")
        with cols[2]:
            outlier_cols = c.get("outlier_columns", [])
            st.metric("Columns with Outliers", len(outlier_cols))
            if outlier_cols:
                st.caption(", ".join(outlier_cols[:4]))
        with cols[3]:
            skewed = c.get("skewed_columns", [])
            st.metric("Highly Skewed Features (|skew|>1)", len(skewed))


# ─── Tab 5: Comparison & Recommendation ──────────────────────────────────────────
def tab_comparison(enabled_tools: dict[str, bool], run_benchmark: bool) -> None:
    st.markdown('<p class="section-header">🏆 Comparison & Recommendation</p>', unsafe_allow_html=True)

    df = st.session_state.get("df")
    eda_results = st.session_state.get("eda_results", {})
    if not eda_results:
        st.info("Run EDA tools first (Tab 2).")
        return

    profile = st.session_state.get("dataset_profile", {})
    tool_insights = st.session_state.get("tool_insights", {})

    # ── IQSE Scoring
    st.subheader("📋 Insight Quality Scores (IQSE)")
    if st.button("Score All Tools (AI)", type="primary"):
        if not os.getenv("GROQ_API_KEY"):
            st.error("Set your Groq API key in the sidebar first.")
        else:
            with st.spinner("AI evaluating each tool's insights …"):
                from modules.iqse import score_all_tools, build_score_table
                scores = score_all_tools(tool_insights, profile)
                st.session_state["iqse_scores"] = scores

    iqse_scores = st.session_state.get("iqse_scores", {})
    if iqse_scores:
        from modules.iqse import build_score_table
        score_rows = build_score_table(iqse_scores)
        score_df = pd.DataFrame(score_rows)

        # Styled dataframe
        def _color_score(val):
            if isinstance(val, (int, float)):
                if val >= 7: return "background-color: rgba(52,211,153,0.15); color:#34d399"
                if val >= 4: return "background-color: rgba(251,191,36,0.15); color:#fbbf24"
                return "background-color: rgba(248,113,113,0.15); color:#f87171"
            return ""

        styled = score_df.style.applymap(_color_score, subset=["Correctness","Relevance","Actionability","Coverage","Overall Score"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # Radar chart
        dims = ["Correctness", "Relevance", "Actionability", "Coverage"]
        fig = go.Figure()
        for row in score_rows:
            fig.add_trace(go.Scatterpolar(
                r=[row[d] for d in dims] + [row[dims[0]]],
                theta=dims + [dims[0]],
                fill="toself",
                name=row["Tool"],
                opacity=0.75,
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            title="Tool Insight Quality — Radar",
            template="plotly_dark",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Benchmarks
    if run_benchmark:
        st.markdown("---")
        st.subheader("⏱ Benchmark Results")
        if st.button("Run Performance Benchmarks"):
            with st.spinner("Benchmarking tools …"):
                from modules.benchmarking import benchmark_all_tools
                bench = benchmark_all_tools(df, str(config.REPORTS_DIR), enabled_tools)
                st.session_state["benchmark_results"] = {
                    t: b.to_dict() for t, b in bench.items()
                }

        bm = st.session_state.get("benchmark_results", {})
        if bm:
            bm_rows = [
                {
                    "Tool": t.capitalize(),
                    "Duration (s)": v.get("duration_sec", 0),
                    "Memory Δ (MB)": v.get("memory_delta_mb", 0),
                    "Status": v.get("status", "?"),
                }
                for t, v in bm.items()
            ]
            bm_df = pd.DataFrame(bm_rows)
            st.dataframe(bm_df, use_container_width=True, hide_index=True)

            fig_bm = px.bar(
                bm_df, x="Tool", y="Duration (s)",
                color="Memory Δ (MB)", text="Duration (s)",
                color_continuous_scale="Viridis",
                title="Runtime vs. Memory Usage",
                template="plotly_dark",
                barmode="group",
            )
            fig_bm.update_traces(texttemplate="%{text:.1f}s", textposition="outside")
            fig_bm.update_layout(height=360)
            st.plotly_chart(fig_bm, use_container_width=True)

    # ── Recommendation
    st.markdown("---")
    st.subheader("🏅 Tool Recommendation")
    if st.button("Get AI Recommendation", type="primary"):
        if not os.getenv("GROQ_API_KEY"):
            st.error("Set your Groq API key in the sidebar first.")
        elif not iqse_scores:
            st.warning("Run IQSE scoring first.")
        else:
            bm = st.session_state.get("benchmark_results", {})
            # If no benchmark, use EDA run times as proxy
            if not bm:
                eda_res = st.session_state.get("eda_results", {})
                bm = {t: r for t, r in eda_res.items()}
            with st.spinner("Gemini generating recommendation …"):
                from modules.recommender import recommend_tool
                rec = recommend_tool(bm, iqse_scores, profile)
                st.session_state["recommendation"] = rec

    rec = st.session_state.get("recommendation", {})
    if rec:
        st.markdown(
            f"""
            <div class="rec-card">
                <h2>🥇 {rec.get('recommended_tool', '?').capitalize()}</h2>
                <p><strong>Confidence:</strong> {rec.get('confidence', '?')} &nbsp;|&nbsp;
                <strong>Score:</strong> {rec.get('overall_winner_score', '?')}/10</p>
                <p>{rec.get('explanation', '')}</p>
                <hr style="border-color: rgba(255,255,255,0.3); margin: 0.75rem 0">
                <p><small>🥈 Runner-up: <strong>{rec.get('runner_up') or 'N/A'}</strong> &nbsp;|&nbsp;
                ⚠️ Avoid: {rec.get('avoid') or 'N/A'}</small></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("Click 'Get AI Recommendation' after running IQSE scoring.")


# ─── Tab 6: Reliability Testing ───────────────────────────────────────────────────
def tab_reliability(enabled_tools: dict[str, bool]) -> None:
    st.markdown('<p class="section-header">🧪 Reliability Testing</p>', unsafe_allow_html=True)

    df = st.session_state.get("df")
    if df is None:
        st.info("Upload a dataset first (Tab 1).")
        return

    st.info(
        "Reliability testing evaluates how well each EDA tool handles "
        "messy real-world data conditions (missing values, noise, imbalance, high cardinality)."
    )

    active_tools = [t for t, en in enabled_tools.items() if en]
    selected_tool = st.selectbox("Select tool to test", active_tools, format_func=str.capitalize)

    rel_rows = st.slider("Max rows for reliability test", 500, 10000, 2000, 500,
                         help="Lower rows = much faster testing.")

    if st.button("▶ Run Reliability Suite", type="primary"):
        from modules.eda_runner import TOOL_RUNNERS
        from modules.reliability_tester import run_reliability_suite, reliability_summary
        runner = TOOL_RUNNERS.get(selected_tool)
        if not runner:
            st.error(f"No runner for {selected_tool}")
            return

        out_base = str(config.REPORTS_DIR / "reliability")
        with st.spinner(f"Running 6 reliability scenarios for {selected_tool} …"):
            results = run_reliability_suite(df, runner, out_base, selected_tool, max_rows=rel_rows)

        current = st.session_state.get("reliability_results", {})
        current[selected_tool] = results
        st.session_state["reliability_results"] = current

    # Display results
    rel_results = st.session_state.get("reliability_results", {})
    for tool, results in rel_results.items():
        from modules.reliability_tester import reliability_summary
        summary = reliability_summary({tool: results})
        s = summary[tool]
        st.markdown(f"#### {tool.capitalize()} — Pass Rate: **{s['pass_rate']}%** ({s['pass_count']}/{s['total_scenarios']})")

        rel_df = pd.DataFrame(results)
        fig = px.bar(
            rel_df, x="scenario", y="duration_sec",
            color="status",
            color_discrete_map={"success": "#34d399", "error": "#f87171"},
            title=f"{tool.capitalize()} — Duration by Scenario",
            template="plotly_dark",
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(rel_df, use_container_width=True, hide_index=True)


# ─── Main ─────────────────────────────────────────────────────────────────────────
def main() -> None:
    _inject_css()
    _init_state()
    enabled_tools, run_benchmark, run_reliability = _sidebar()

    st.markdown(
        f"<h1 style='text-align:center; color:#a78bfa; font-size:2rem;'>🔬 {config.APP_TITLE}</h1>"
        "<p style='text-align:center; color:#94a3b8; margin-top:-0.5rem;'>"
        "Automatically benchmark EDA tools · Score insights with AI · Get the best tool for your data"
        "</p><hr style='border-color: rgba(167,139,250,0.2)'>",
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "📁 Upload & Preview",
        "🔬 Run EDA Tools",
        "📊 View Reports",
        "🤖 AI Analysis",
        "🏆 Comparison & Recommendation",
        "🧪 Reliability Testing",
    ])

    with tabs[0]: tab_upload()
    with tabs[1]: tab_run_eda(enabled_tools)
    with tabs[2]: tab_reports()
    with tabs[3]: tab_ai_analysis()
    with tabs[4]: tab_comparison(enabled_tools, run_benchmark)
    with tabs[5]: tab_reliability(enabled_tools)


if __name__ == "__main__":
    main()
