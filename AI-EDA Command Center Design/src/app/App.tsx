import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { SidebarNav } from "./components/sidebar-nav";
import { DataHubTab } from "./components/data-hub-tab";
import { InsightsAuditTab } from "./components/insights-audit-tab";
import { BenchmarkingTab } from "./components/benchmarking-tab";
import { ToolRecommenderTab } from "./components/tool-recommender-tab";
import { ReliabilitySuiteTab } from "./components/reliability-suite-tab";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Database, Brain, Trophy, Star, Shield, Loader2 } from "lucide-react";
import { api } from "./api";

export default function App() {
  const [selectedTools, setSelectedTools] = useState<string[]>(["ydata", "sweetviz", "autoviz"]);
  const [activeTab, setActiveTab] = useState("data-hub");
  const [isLoading, setIsLoading] = useState(false);

  // Analysis State
  const [datasetProfile, setDatasetProfile] = useState<any>(null);
  const [edaResults, setEdaResults] = useState<any>(null);
  const [aiInsights, setAiInsights] = useState<any>(null);
  const [benchmarkData, setBenchmarkData] = useState<any>(null);
  const [scores, setScores] = useState<any>(null);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [reliabilityResults, setReliabilityResults] = useState<any>(null);
  const [isReliabilityLoading, setIsReliabilityLoading] = useState(false);

  const toggleTool = (tool: string) => {
    setSelectedTools((prev) =>
      prev.includes(tool) ? prev.filter((t) => t !== tool) : [...prev, tool]
    );
  };

  const handleUpload = async (file: File) => {
    setIsLoading(true);
    try {
      const response = await api.upload(file);
      // Normalize the backend response into a flat profile object for the UI
      const rawProfile = response.profile || {};
      const totalCells = (rawProfile.n_rows || 0) * (rawProfile.n_cols || 0);
      const missingCells = Math.round((rawProfile.total_missing_pct || 0) / 100 * totalCells);
      const healthScore = Math.round(100 - (rawProfile.total_missing_pct || 0));
      const normalized = {
        file_name: response.file_name,
        observations: rawProfile.n_rows,
        features: rawProfile.n_cols,
        missing_cells: missingCells,
        health_score: healthScore,
        sample_data: response.sample_data,
        // Keep all raw fields for AI/scoring use
        raw: rawProfile,
      };
      setDatasetProfile(normalized);
      setActiveTab("data-hub");
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const runAnalysis = async () => {
    if (!datasetProfile) return;
    setIsLoading(true);
    try {
      const results = await api.runEda(selectedTools);
      setEdaResults(results);
      
      const insights = await api.getAIInsights();
      setAiInsights(insights);
      
      // /insights/score returns { scores: {...}, table: [...] }
      // Extract the inner scores dict which is keyed by tool name
      const iqseResponse = await api.scoreInsights();
      const iqseScores = iqseResponse?.scores || iqseResponse || {};
      setScores(iqseScores);
      
      const rec = await api.getRecommendation();
      setRecommendation(rec);
      
      const benchmarks = await api.runBenchmark();
      setBenchmarkData(benchmarks);
    } catch (err: any) {
      console.error("Pipeline error:", err?.message || err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunReliability = async (tool: string) => {
    setIsReliabilityLoading(true);
    try {
      const results = await api.runReliability(tool);
      setReliabilityResults(results);
    } catch (err) {
      console.error(err);
    } finally {
      setIsReliabilityLoading(false);
    }
  };

  const tabs = [
    { id: "data-hub", label: "Data Hub", icon: Database },
    { id: "insights", label: "Insights Audit", icon: Brain },
    { id: "benchmarking", label: "Benchmarking", icon: Trophy },
    { id: "recommender", label: "Recommender", icon: Star },
    { id: "reliability", label: "Reliability", icon: Shield },
  ];

  return (
    <div className="dark min-h-screen flex bg-[var(--deep-space-blue)]">
      <SidebarNav selectedTools={selectedTools} onToggleTool={toggleTool} />

      <main className="flex-1 overflow-y-auto">
        {/* Ambient background: aurora blobs + holographic grid */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="bg-grid absolute inset-0 opacity-70" />
          <div className="aurora-blob absolute -top-24 right-0 w-[560px] h-[560px] bg-[var(--electric-violet)]/25 rounded-full blur-[130px]" />
          <div className="aurora-blob-slow absolute bottom-0 left-0 w-[520px] h-[520px] bg-[var(--cyber-cyan)]/15 rounded-full blur-[130px]" />
          <div className="aurora-blob absolute top-1/3 left-1/2 w-[420px] h-[420px] bg-[var(--neon-green)]/10 rounded-full blur-[140px]" />
        </div>

        <div className="relative z-10 p-8">
          <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="mb-8">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-4">
              <div>
                <h1 className="text-4xl font-display font-bold text-gradient mb-2 leading-tight">
                  Automated EDA Benchmarking &amp; Evaluation
                </h1>
                <p className="text-white/50 font-mono text-xs uppercase tracking-[0.3em]">AI Command Center · v1.0</p>
              </div>
              <div className="flex items-center gap-4">
                {(isLoading || isReliabilityLoading) && (
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg glass">
                    <Loader2 className="w-4 h-4 text-[var(--cyber-cyan)] animate-spin" />
                    <span className="text-xs font-mono uppercase tracking-wider shimmer">Processing</span>
                  </div>
                )}
                <div className="px-4 py-2 rounded-lg backdrop-blur-sm bg-[var(--neon-green)]/15 border border-[var(--neon-green)]/30 shadow-[0_0_24px_rgba(52,211,153,0.15)]">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--neon-green)] opacity-60" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--neon-green)]" />
                    </span>
                    <span className="text-sm text-[var(--neon-green)] uppercase font-bold tracking-wide">System Online</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="w-full justify-start mb-6 backdrop-blur-xl bg-white/[0.04] border border-white/10 p-1.5 h-auto gap-1.5 rounded-xl">
              {tabs.map((tab) => (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  className="text-white/50 data-[state=active]:bg-gradient-to-r data-[state=active]:from-[var(--electric-violet)] data-[state=active]:to-[var(--cyber-cyan)] data-[state=active]:text-white data-[state=active]:shadow-[0_4px_20px_rgba(139,92,246,0.35)] px-6 py-3 rounded-lg transition-all duration-300 hover:text-white/90"
                >
                  <div className="flex items-center gap-2">
                    <tab.icon className="w-4 h-4" />
                    <span className="uppercase text-[11px] font-bold tracking-widest">{tab.label}</span>
                  </div>
                </TabsTrigger>
              ))}
            </TabsList>

            <AnimatePresence mode="wait">
              <TabsContent value="data-hub" className="mt-0">
                <DataHubTab profile={datasetProfile} onUpload={handleUpload} onRun={runAnalysis} loading={isLoading} />
              </TabsContent>
              <TabsContent value="insights" className="mt-0">
                <InsightsAuditTab insights={aiInsights} />
              </TabsContent>
              <TabsContent value="benchmarking" className="mt-0">
                <BenchmarkingTab data={benchmarkData} scores={scores} />
              </TabsContent>
              <TabsContent value="recommender" className="mt-0">
                <ToolRecommenderTab recommendation={recommendation} scores={scores} />
              </TabsContent>
              <TabsContent value="reliability" className="mt-0">
                <ReliabilitySuiteTab results={reliabilityResults} onRunReliability={handleRunReliability} loading={isReliabilityLoading} />
              </TabsContent>
            </AnimatePresence>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
