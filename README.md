# 🤖 AI-EDA Command Center

<div align="center">

![AI-EDA Command Center](https://img.shields.io/badge/AI--EDA-Command%20Center-blueviolet?style=for-the-badge&logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Groq](https://img.shields.io/badge/Groq-AI-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)

**A production-grade, AI-powered Automated EDA Benchmarking & Evaluation Platform**

*Compare EDA tools head-to-head, generate AI narratives, detect insight gaps, and get dataset-aware recommendations — all in a stunning real-time dashboard.*

</div>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                  │
│         Neon-styled dashboard • Real-time state          │
│          http://localhost:5173                           │
└────────────────────┬────────────────────────────────────┘
                     │ REST API (JSON)
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                          │
│          http://localhost:8000                           │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  ydata   │  │ Sweetviz │  │ AutoViz  │  │  Lux   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│                                                          │
│              Groq AI (llama-3.3-70b-versatile)           │
│   Narratives • IQSE Scoring • Gap Detection • Recs      │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Tab | Capability |
|-----|-----------|
| 📁 **Data Hub** | Upload any CSV → instant profiling (rows, columns, missingness, health score) + live data preview |
| 🧠 **Insights Audit** | Groq-generated narrative summary + cross-tool gap detection |
| 🏆 **Benchmarking** | Radar chart comparing Speed, Memory, Correctness, Relevance, Coverage |
| 🎯 **Recommender** | Dataset-aware best-tool recommendation with confidence score and reasoning |
| 🛡️ **Reliability Suite** | Adversarial stress testing — noise injection, missingness simulation, stability scoring |

---

## 📂 Project Structure

```
Automated EDA/
├── server.py                        # FastAPI REST API (main backend)
├── config.py                        # Global settings, Groq config
├── requirements.txt
├── .env.example                     # API key template
├── generate_sample_data.py          # Creates 4 sample CSV datasets
│
├── modules/
│   ├── data_loader.py               # CSV loading + dataset profiling + JSON sanitizer
│   ├── eda_runner.py                # Runs ydata, Sweetviz, AutoViz, Lux
│   ├── insight_extractor.py         # Parses tool outputs → unified schema
│   ├── ai_insight_generator.py      # Groq narrative generation
│   ├── iqse.py                      # AI Insight Quality Scoring Engine
│   ├── gap_detector.py              # Cross-tool gap analysis
│   ├── benchmarking.py              # Runtime + memory benchmarks
│   ├── recommender.py               # Dataset-aware best-tool recommendation
│   └── reliability_tester.py        # Adversarial stress testing
│
├── AI-EDA Command Center Design/    # Vite + React frontend
│   ├── src/app/
│   │   ├── App.tsx                  # Global state orchestration
│   │   ├── api.ts                   # Unified API client
│   │   └── components/              # All UI tabs and components
│   ├── package.json
│   └── vite.config.ts
│
├── data/                            # Sample + uploaded datasets
└── reports/                         # Auto-generated EDA reports (HTML, PNG)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free [Groq API Key](https://console.groq.com/)

### 1. Clone the repository

```bash
git clone https://github.com/Abhi241-bot/ai-eda-command-center.git
cd ai-eda-command-center
```

### 2. Set up the Python backend

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
copy .env.example .env
```

Edit `.env` and add your Groq API key:
```
GROQ_API_KEY=gsk_your_key_here
```

> Get a free key at [console.groq.com](https://console.groq.com/) — no credit card required.

### 4. Generate sample datasets (optional)

```bash
python generate_sample_data.py
```

### 5. Start the backend

```bash
python server.py
```
Backend runs at **http://localhost:8000**

### 6. Start the frontend (new terminal)

```bash
cd "AI-EDA Command Center Design"
npm install
npm run dev
```
Frontend runs at **http://localhost:5173**

### 7. Open the dashboard

Navigate to **http://localhost:5173** and start uploading your CSV files!

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Powers all AI features (narrative, scoring, gaps, recs) |

---

## 🧬 EDA Tools Evaluated

| Tool | Description | Output |
|------|-------------|--------|
| **ydata-profiling** | Comprehensive statistical report | HTML + JSON |
| **Sweetviz** | Beautiful comparative EDA | HTML report |
| **AutoViz** | Automatic chart generation | PNG charts |
| **Lux** | Smart visualization recommendations | JSON (Jupyter only) |

---

## 📊 Sample Datasets

Run `python generate_sample_data.py` to create:

| File | Description |
|------|-------------|
| `sample_clean.csv` | 1000-row Titanic-style, clean & balanced |
| `sample_noisy.csv` | Same with 20% noise + 20% random missing |
| `sample_imbalanced.csv` | 95/5 class split on target column |
| `sample_high_cardinality.csv` | 500+ unique-value string columns |

---

## 🧩 Module API Reference

### Data Loading
```python
from modules.data_loader import load_dataset, get_dataset_profile

df = load_dataset("data/sample_clean.csv")
profile = get_dataset_profile(df)  # Returns JSON-safe dict
```

### Running EDA Tools
```python
from modules.eda_runner import run_all_tools

results = run_all_tools(df, "reports/", enabled_tools={
    "ydata": True, "sweetviz": True, "autoviz": True, "lux": False
})
```

### IQSE Scoring
```python
from modules.iqse import score_all_tools, build_score_table

scores = score_all_tools(tool_insights, profile)
table = build_score_table(scores)
```

### Tool Recommendation
```python
from modules.recommender import recommend_tool

rec = recommend_tool(benchmarks, iqse_scores, profile)
print(rec["recommended_tool"])   # e.g. "ydata"
print(rec["confidence"])         # "High" | "Medium" | "Low"
print(rec["explanation"])        # AI-generated reasoning
```

### Reliability Testing
```python
from modules.reliability_tester import run_reliability_suite, reliability_summary

results = run_reliability_suite(df, runner_fn, output_dir, tool_name)
summary = reliability_summary({tool_name: results})
```

---

## ⚠️ Known Limitations

- **Lux** requires a Jupyter kernel and is disabled by default. Enable in `config.py` if needed.
- **AutoViz** uses matplotlib's non-interactive `Agg` backend and saves charts to `reports/autoviz/`.
- The backend holds state in memory per-session. Restart the server to reset the analysis state.
- NumPy 2.x compatibility patch is applied automatically in `eda_runner.py` for Sweetviz support.

---

## 🏛️ Tech Stack

**Backend:** Python · FastAPI · Uvicorn · Pandas · ydata-profiling · Sweetviz · AutoViz · Groq SDK

**Frontend:** React · Vite · TypeScript · Framer Motion · Recharts · Lucide Icons · Tailwind CSS

**AI:** Groq API (`llama-3.3-70b-versatile`) — sub-second inference, no rate limits on free tier

---

## 📜 License

MIT — free for personal and commercial use.

---

<div align="center">
Built with ❤️ using FastAPI + React + Groq AI
</div>
