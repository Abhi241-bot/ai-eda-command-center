import { motion } from "motion/react";
import { AlertTriangle, Brain, Sparkles, FileSearch } from "lucide-react";

interface InsightsAuditTabProps {
  insights: {
    narrative: string;
    gaps: string[];
  } | null;
}

export function InsightsAuditTab({ insights }: InsightsAuditTabProps) {
  const severityColors: Record<string, string> = {
    high: "var(--soft-coral)",
    medium: "#f59e0b",
    low: "#34d399",
  };

  const narrativeLines = insights?.narrative 
    ? insights.narrative.split("\n").filter(l => l.trim().length > 0)
    : [];

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Left Column - AI Narrative Summary */}
      <motion.div
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="space-y-4"
      >
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-[var(--electric-violet)]" />
          <h3 className="text-lg text-white">AI Narrative Summary</h3>
          <Sparkles className="w-4 h-4 text-[var(--neon-green)]" />
        </div>

        <div className="p-6 rounded-xl backdrop-blur-sm bg-gradient-to-br from-[var(--deep-space-blue)]/80 to-[var(--electric-violet)]/20 border border-[var(--electric-violet)]/30 min-h-[400px]">
          {!insights ? (
            <div className="h-full flex flex-col items-center justify-center text-white/40 gap-4">
              <FileSearch className="w-12 h-12 opacity-20" />
              <p>Run analysis to generate AI insights</p>
            </div>
          ) : (
            <div className="font-mono text-sm space-y-4 text-white/90">
              {narrativeLines.map((line, i) => (
                <motion.p
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <span className="text-[var(--neon-green)] mr-2">▸</span>
                  {line.startsWith("-") || line.startsWith("*") ? line.substring(1).trim() : line}
                </motion.p>
              ))}
              
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                className="pt-4 border-t border-white/10 flex items-center justify-between"
              >
                <span className="text-xs text-white/60">Groq Engine v3.3</span>
                <span className="text-xs text-[var(--neon-green)]">● READY</span>
              </motion.div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Right Column - Insight Gap Detection */}
      <motion.div
        initial={{ x: 20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="space-y-4"
      >
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-[var(--soft-coral)]" />
          <h3 className="text-lg text-white">Insight Gap Detection</h3>
        </div>

        <div className="space-y-3 min-h-[300px]">
          {!insights || insights.gaps.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-white/20 border border-white/5 rounded-xl p-12">
              <AlertTriangle className="w-8 h-8 mb-2 opacity-10" />
              <p className="text-sm">No significant gaps detected between tools</p>
            </div>
          ) : (
            insights.gaps.map((gap, index) => {
              // Try to extract tool and severity from the gap string if possible, otherwise defaults
              const severity = gap.toLowerCase().includes("critical") ? "high" : "medium";
              return (
                <motion.div
                  key={index}
                  initial={{ x: 20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ x: -4 }}
                  className="relative group"
                >
                  <div
                    className="absolute inset-0 rounded-lg blur-md opacity-20"
                    style={{ backgroundColor: severityColors[severity] }}
                  />
                  <div className="relative p-4 rounded-lg backdrop-blur-sm bg-white/5 border border-white/10 group-hover:border-[var(--soft-coral)]/40 transition-all duration-300">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: severityColors[severity] }} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                           <span className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--soft-coral)]/10 text-[var(--soft-coral)]">
                            DETECTED GAP
                          </span>
                        </div>
                        <p className="text-sm text-white/90">{gap}</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>

        {/* Summary Card */}
        {insights && insights.gaps.length > 0 && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="p-6 rounded-xl backdrop-blur-sm bg-gradient-to-br from-[var(--soft-coral)]/10 to-transparent border border-[var(--soft-coral)]/30"
          >
            <h4 className="text-sm text-white/60 mb-3">Gap Analysis Summary</h4>
            <div className="flex items-end gap-2">
              <div className="text-3xl font-mono text-[var(--soft-coral)]">{insights.gaps.length}</div>
              <div className="text-xs text-white/60 mb-1">Functional discrepancies found across the EDA toolchain</div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
