"""
server.py — FastAPI Backend
─────────────────────────────
REST API for the AI-Enhanced Automated EDA Benchmarking System.
Bridges the existing Python modules to the new React frontend.
"""

import os
import time
import shutil
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from modules.data_loader import get_dataset_profile, sanitize_val
from modules.eda_runner import TOOL_RUNNERS, run_all_tools
from modules.insight_extractor import (
    extract_ydata_insights, extract_sweetviz_insights,
    extract_autoviz_insights, extract_lux_insights, unify_insights
)
from modules.ai_insight_generator import generate_narrative
from modules.gap_detector import detect_gaps
from modules.iqse import score_all_tools, build_score_table
from modules.benchmarking import benchmark_all_tools
from modules.reliability_tester import run_reliability_suite, reliability_summary

# ─── Setup ───────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI(title="AI-EDA Backend API")

# Enable CORS for the React frontend (usually runs on :5173 or :3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (simplified for this project)
class AppState:
    df: Optional[pd.DataFrame] = None
    file_name: str = ""
    profile: Optional[Dict] = None
    eda_results: Dict = {}
    tool_insights: Dict = {}
    unified: Optional[Dict] = None
    iqse_scores: Dict = {}

state = AppState()

# ─── Models ──────────────────────────────────────────────────────────────────────

class EdaRequest(BaseModel):
    tools: List[str]

class ReliabilityRequest(BaseModel):
    tool: str
    max_rows: int = 2000

# ─── Endpoints ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "online", "message": "AI-EDA Backend API is running"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV and return basic profile."""
    try:
        temp_path = config.DATA_DIR / file.filename
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        df = pd.read_csv(temp_path)
        state.df = df
        state.file_name = file.filename
        state.profile = get_dataset_profile(df)
        
        response = {
            "file_name": state.file_name,
            "profile": state.profile,
            "sample_data": df.head(10).to_dict(orient="records")
        }
        return sanitize_val(response)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_eda")
async def run_eda(req: EdaRequest):
    """Trigger the selected EDA tools."""
    if state.df is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded")
    
    enabled = {t: (t in req.tools) for t in ["ydata", "sweetviz", "autoviz", "lux"]}
    try:
        results = run_all_tools(state.df, config.REPORTS_DIR, enabled)
        state.eda_results = results
        
        # Extract insights immediately
        tool_insights = {}
        # ydata
        yr = results.get("ydata", {})
        if yr.get("json_path"):
            tool_insights["ydata"] = extract_ydata_insights(yr["json_path"])
        # sweetviz
        if results.get("sweetviz", {}).get("status") == "success":
            tool_insights["sweetviz"] = extract_sweetviz_insights(state.df)
        # autoviz
        if results.get("autoviz", {}).get("status") == "success":
            tool_insights["autoviz"] = extract_autoviz_insights(state.df, config.REPORTS_DIR / "autoviz")
        
        state.tool_insights = tool_insights
        state.unified = unify_insights(tool_insights)
        
        logger.info(f"Extracted insights for tools: {list(tool_insights.keys())}")
        return sanitize_val({"results": results, "unified": state.unified})
    except Exception as e:
        logger.error(f"EDA Run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights/ai")
async def get_ai_insights():
    """Generate AI narrative and gaps."""
    if state.unified is None:
        raise HTTPException(status_code=400, detail="Run EDA first to generate insights")
    
    import os
    if not os.getenv("GROQ_API_KEY"):
        return {"error": "API Key missing"}

    narrative = generate_narrative(state.profile, state.unified)
    gaps = detect_gaps(state.unified, state.profile)
    
    return sanitize_val({"narrative": narrative, "gaps": gaps})

@app.get("/insights/score")
async def score_insights():
    """Score the insights with AI."""
    if not state.tool_insights:
        # Fallback: if we have a dataframe, try to extract a minimal set of insights now
        if state.df is not None:
            logger.info("tool_insights empty, attempting on-the-fly extraction from dataframe")
            state.tool_insights = {"autoviz": extract_autoviz_insights(state.df, config.REPORTS_DIR / "autoviz")}
            state.unified = unify_insights(state.tool_insights)
        else:
            raise HTTPException(status_code=400, detail="Run EDA first to generate insights for scoring")
    
    scores = score_all_tools(state.tool_insights, state.profile)
    state.iqse_scores = scores
    return sanitize_val({"scores": scores, "table": build_score_table(scores)})

@app.get("/recommendation")
async def get_recommendation():
    """Get the AI tool recommendation."""
    if not state.iqse_scores:
        raise HTTPException(status_code=400, detail="Score insights first")
    
    from modules.recommender import recommend_tool
    # Use eda_results for benchmark data if full benchmark wasn't run
    rec = recommend_tool(state.eda_results, state.iqse_scores, state.profile)
    return sanitize_val(rec)

@app.post("/reliability")
async def run_reliability(req: ReliabilityRequest):
    """Run reliability suite for a specific tool."""
    if state.df is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded")
    
    runner = TOOL_RUNNERS.get(req.tool)
    if not runner:
        raise HTTPException(status_code=404, detail=f"Tool {req.tool} not found")
        
    out_base = str(config.REPORTS_DIR / "reliability")
    results = run_reliability_suite(state.df, runner, out_base, req.tool, max_rows=req.max_rows)
    summary = reliability_summary({req.tool: results})
    
    # Calculate a simple score (percentage of successful tests)
    passes = sum(1 for r in results if r.get("status") == "Pass")
    score = passes / len(results) if results else 0
    
    return {
        "results": results, 
        "summary": summary.get(req.tool, "No summary available"),
        "score": score
    }

@app.get("/benchmark")
async def run_benchmark():
    """Run performance benchmarks."""
    logger.info("Starting benchmarking...")
    if state.df is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded")
    
    enabled = {t: True for t in ["ydata", "sweetviz", "autoviz"]} # subset for speed
    try:
        bench = benchmark_all_tools(state.df, str(config.REPORTS_DIR), enabled)
        logger.info(f"Benchmarking complete for tools: {list(bench.keys())}")
        return sanitize_val({t: b.to_dict() for t, b in bench.items()})
    except Exception as e:
        logger.error(f"Benchmarking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
