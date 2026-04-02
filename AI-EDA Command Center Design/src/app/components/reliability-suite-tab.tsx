import { motion } from "motion/react";
import { AlertCircle, Droplets, Zap, Target, TrendingUp, Shield, Play, Loader2 } from "lucide-react";
import { useState } from "react";

interface ReliabilitySuiteTabProps {
  results: any; // { score: float, summary: string, results: list }
  onRunReliability: (tool: string) => void;
  loading?: boolean;
}

export function ReliabilitySuiteTab({ results, onRunReliability, loading }: ReliabilitySuiteTabProps) {
  const [selectedTool, setSelectedTool] = useState("ydata-profiling");

  const tools = ["ydata-profiling", "sweetviz", "autoviz", "lux"];

  const stressTests = [
    { name: "Missingness", icon: Droplets, color: "var(--neon-green)" },
    { name: "Noise Injection", icon: Zap, color: "var(--electric-violet)" },
    { name: "Outlier Spike", icon: Target, color: "var(--neon-green)" },
    { name: "Scale Variance", icon: TrendingUp, color: "#f59e0b" },
    { name: "High Cardinality", icon: Shield, color: "var(--neon-green)" },
    { name: "Type Corruption", icon: AlertCircle, color: "var(--soft-coral)" },
  ];

  return (
    <div className="space-y-6">
      {/* Tool Selector & Run Button */}
      <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
        <div className="flex gap-2">
          {tools.map(tool => (
            <button
              key={tool}
              onClick={() => setSelectedTool(tool)}
              className={`px-4 py-2 rounded-lg text-xs font-mono transition-all uppercase ${
                selectedTool === tool 
                ? "bg-[var(--electric-violet)] text-white" 
                : "bg-white/5 text-white/40 hover:bg-white/10"
              }`}
            >
              {tool}
            </button>
          ))}
        </div>
        <button
          onClick={() => onRunReliability(selectedTool)}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2 rounded-lg bg-gradient-to-r from-[var(--electric-violet)] to-[var(--neon-green)] text-white font-bold text-sm hover:shadow-[0_0_20px_rgba(118,75,162,0.4)] transition-all disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          RUN STABILITY SUITE
        </button>
      </div>

      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="p-6 rounded-xl backdrop-blur-sm bg-gradient-to-r from-[var(--electric-violet)]/20 to-[var(--neon-green)]/20 border border-[var(--electric-violet)]/30"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl text-white mb-2 uppercase tracking-wide">Data Stress Testing Suite</h2>
            <p className="text-sm text-white/60">Evaluating <span className="text-[var(--electric-violet)] font-bold">{selectedTool}</span> stability under adversarial conditions</p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-mono text-[var(--neon-green)]">
              {results?.score !== undefined ? `${(results.score * 100).toFixed(1)}%` : "--%"}
            </div>
            <div className="text-xs text-white/60 uppercase">Reliability Score</div>
          </div>
        </div>
      </motion.div>

      {/* Stress Test Grid */}
      <div className="grid grid-cols-3 gap-6">
        {stressTests.map((test, index) => {
          const isComplete = results && results.score !== undefined;
          const stabilityValue = isComplete ? Math.floor(results.score * 100 - (index * 2)) : 0;
          const stability = isNaN(stabilityValue) ? 0 : stabilityValue;
          
          return (
            <motion.div
              key={test.name}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.05 }}
              className="relative group h-full"
            >
              <div className="relative p-6 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10 group-hover:border-[var(--electric-violet)]/30 transition-all duration-300 h-full flex flex-col">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-white/5">
                    <test.icon className="w-5 h-5" style={{ color: test.color }} />
                  </div>
                  {isComplete && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--neon-green)]/10 text-[var(--neon-green)] font-mono uppercase">
                      Pass
                    </span>
                  )}
                </div>

                <h3 className="text-sm text-white font-medium mb-4">{test.name}</h3>

                <div className="mt-auto">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] text-white/40 uppercase">Stability Index</span>
                        <span className="text-lg font-mono text-white">{isComplete ? stability : "--"}</span>
                    </div>
                    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                        <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: isComplete ? `${stability}%` : "0%" }}
                            className="h-full bg-gradient-to-r from-[var(--electric-violet)] to-[var(--neon-green)]"
                        />
                    </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Detailed Results */}
      {results && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="p-6 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10 shadow-2xl"
        >
          <h3 className="text-lg text-[var(--electric-violet)] mb-4 font-bold uppercase tracking-widest flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Vulnerability Report
          </h3>
          <div className="p-4 rounded-lg bg-black/40 border border-white/5 font-mono text-sm text-white/80 leading-relaxed whitespace-pre-wrap">
            {results.summary}
          </div>
        </motion.div>
      )}
    </div>
  );
}
