/**
 * api.ts
 * ────────
 * Unified API service for the AI-EDA Command Center.
 * Communicates with the FastAPI backend (http://localhost:8000).
 */

const API_BASE = "http://localhost:8000";

export interface DatasetProfile {
  file_name: string;
  profile: any;
  sample_data: any[];
}

export interface EdaResult {
  results: any;
  unified: any;
}

export interface AIInsights {
  narrative: string;
  gaps: string[];
}

export interface BenchmarkingResults {
  [tool: string]: any;
}

export const api = {
  /** Upload a CSV file */
  async upload(file: File): Promise<DatasetProfile> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("Upload failed");
    return res.json();
  },

  /** Run selected EDA tools */
  async runEda(tools: string[]): Promise<EdaResult> {
    const res = await fetch(`${API_BASE}/run_eda`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tools }),
    });
    if (!res.ok) throw new Error("EDA run failed");
    return res.json();
  },

  /** Get AI narrative and gaps */
  async getAIInsights(): Promise<AIInsights> {
    const res = await fetch(`${API_BASE}/insights/ai`);
    if (!res.ok) throw new Error("AI insights failed");
    return res.json();
  },

  /** Score insights with AI */
  async scoreInsights(): Promise<any> {
    const res = await fetch(`${API_BASE}/insights/score`);
    if (!res.ok) throw new Error("Scoring failed");
    return res.json();
  },

  /** Get tool recommendation */
  async getRecommendation(): Promise<any> {
    const res = await fetch(`${API_BASE}/recommendation`);
    if (!res.ok) throw new Error("Recommendation failed");
    return res.json();
  },

  /** Run reliability suite */
  async runReliability(tool: string, maxRows: number = 2000): Promise<any> {
    const res = await fetch(`${API_BASE}/reliability`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool, max_rows: maxRows }),
    });
    if (!res.ok) throw new Error("Reliability test failed");
    return res.json();
  },

  /** Run benchmarks */
  async runBenchmark(): Promise<BenchmarkingResults> {
    const res = await fetch(`${API_BASE}/benchmark`);
    if (!res.ok) throw new Error("Benchmarking failed");
    return res.json();
  },
};
