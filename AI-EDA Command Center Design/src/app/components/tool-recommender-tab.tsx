import { motion } from "motion/react";
import { Star, CheckCircle2, Zap, Target, HelpCircle, AlertTriangle, TrendingUp } from "lucide-react";

interface ToolRecommenderTabProps {
  recommendation: any;
  scores: any;
}

const CONFIDENCE_MAP: Record<string, number> = {
  High: 90,
  Medium: 60,
  Low: 30,
};

export function ToolRecommenderTab({ recommendation, scores }: ToolRecommenderTabProps) {
  if (!recommendation) {
    return (
      <div className="glass max-w-4xl mx-auto p-20 flex flex-col items-center justify-center text-white/30 rounded-2xl gap-4">
        <HelpCircle className="w-16 h-16 text-[var(--cyber-cyan)]/30 animate-float" />
        <p className="font-mono text-sm uppercase tracking-wider">Run analysis to see tool recommendations</p>
      </div>
    );
  }

  // The backend returns: recommended_tool, confidence (High/Medium/Low),
  // overall_winner_score, explanation, runner_up, avoid
  const bestTool = recommendation.recommended_tool || recommendation.best_tool || "Unknown";
  const confidenceLabel = recommendation.confidence || "Low";
  const confidencePct = CONFIDENCE_MAP[confidenceLabel] ?? 30;
  const explanation = recommendation.explanation || "";
  const runnerUp = recommendation.runner_up;
  const avoid = recommendation.avoid;
  const winnerScore = recommendation.overall_winner_score;

  // Build per-tool score rows. `scores` may arrive as a prebuilt table
  // ({ table: [...] }), wrapped ({ scores: {...} }), or as the raw dict keyed
  // by tool name — handle all three shapes.
  const scoresDict = scores?.scores || (scores && !scores.table ? scores : {});
  const scoreEntries = scores?.table || Object.entries(scoresDict).map(([name, s]: [string, any]) => ({
    Tool: name.charAt(0).toUpperCase() + name.slice(1),
    "Overall Score": s?.overall ?? 0,
    Correctness: s?.correctness ?? 0,
    Relevance: s?.relevance ?? 0,
    Coverage: s?.coverage ?? 0,
  }));

  const bestToolRow = scoreEntries?.find((r: any) =>
    r.Tool?.toLowerCase() === bestTool?.toLowerCase()
  );

  const alternatives = (scoreEntries || []).filter(
    (r: any) => r.Tool?.toLowerCase() !== bestTool?.toLowerCase()
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Confidence Meter */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="p-6 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-[var(--electric-violet)]" />
            <h3 className="text-lg text-white">Recommendation Confidence</h3>
          </div>
          <div className="text-3xl font-mono text-[var(--neon-green)]">{confidenceLabel}</div>
        </div>
        <div className="relative h-3 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${confidencePct}%` }}
            transition={{ delay: 0.3, duration: 1.2, ease: "easeOut" }}
            className="h-full bg-gradient-to-r from-[var(--electric-violet)] via-[var(--neon-green)] to-[var(--neon-green)]"
          />
        </div>
      </motion.div>

      {/* Golden Card */}
      <motion.div
        initial={{ y: 30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6 }}
        className="relative group"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--electric-violet)]/40 via-[var(--neon-green)]/40 to-[var(--electric-violet)]/40 rounded-2xl blur-2xl group-hover:blur-3xl transition-all duration-500" />
        
        <div className="relative p-8 rounded-2xl backdrop-blur-xl bg-gradient-to-br from-[var(--deep-space-blue)]/90 to-[var(--electric-violet)]/30 border-2 border-[var(--electric-violet)]/50">
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Star className="w-6 h-6 text-[#FFD700] fill-[#FFD700]" />
                <span className="text-xs uppercase tracking-wider text-[var(--neon-green)]">Top Rated Choice</span>
              </div>
              <h2 className="text-4xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent uppercase font-mono">
                {bestTool}
              </h2>
            </div>
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
              className="w-20 h-20 rounded-full bg-gradient-to-br from-[var(--electric-violet)] to-[var(--neon-green)] flex items-center justify-center shadow-lg"
            >
              <Zap className="w-10 h-10 text-white fill-white" />
            </motion.div>
          </div>

          {/* Score Grid */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <div className="text-2xl font-mono text-[var(--neon-green)]">
                {winnerScore != null ? winnerScore.toFixed(1) : (bestToolRow?.["Overall Score"] ?? "—")}
              </div>
              <div className="text-[10px] text-white/40 uppercase mt-1">IQSE Score</div>
            </div>
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <div className="text-2xl font-mono text-[var(--neon-green)]">
                {bestToolRow ? `${(bestToolRow["Coverage"] * 10).toFixed(0)}%` : "—"}
              </div>
              <div className="text-[10px] text-white/40 uppercase mt-1">Coverage</div>
            </div>
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <div className="text-2xl font-mono text-[var(--neon-green)]">
                {bestToolRow ? `${(bestToolRow["Correctness"] * 10).toFixed(0)}%` : "—"}
              </div>
              <div className="text-[10px] text-white/40 uppercase mt-1">Correctness</div>
            </div>
          </div>

          {/* Explanation */}
          <div className="mb-6">
            <h3 className="text-lg text-white mb-4 flex items-center gap-2 font-medium">
              <CheckCircle2 className="w-5 h-5 text-[var(--neon-green)]" />
              AI Recommendation Reasoning
            </h3>
            <div className="p-4 rounded-lg bg-white/5 border border-white/5">
              <p className="text-sm text-white/80 leading-relaxed">{explanation || "No explanation available."}</p>
            </div>
          </div>

          {/* Runner-up and Avoid */}
          <div className="grid grid-cols-2 gap-4">
            {runnerUp && (
              <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex items-start gap-3">
                <TrendingUp className="w-4 h-4 text-[var(--neon-green)] mt-1 flex-shrink-0" />
                <div>
                  <div className="text-[10px] text-white/40 uppercase mb-1">Runner-Up</div>
                  <div className="text-sm text-white font-mono uppercase">{runnerUp}</div>
                </div>
              </div>
            )}
            {avoid && (
              <div className="p-4 rounded-lg bg-white/5 border border-[var(--soft-coral)]/20 flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-[var(--soft-coral)] mt-1 flex-shrink-0" />
                <div>
                  <div className="text-[10px] text-white/40 uppercase mb-1">Avoid</div>
                  <p className="text-sm text-white/70 leading-relaxed">{avoid}</p>
                </div>
              </div>
            )}
          </div>

          <motion.div className="mt-6 w-full py-4 rounded-lg bg-gradient-to-r from-[var(--electric-violet)] to-[var(--neon-green)] text-white text-center font-bold tracking-wider shadow-lg uppercase">
            Deploy {bestTool} Profile
          </motion.div>
        </div>
      </motion.div>

      {/* Alternative Options */}
      {alternatives.length > 0 && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="p-6 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10"
        >
          <h3 className="text-sm text-white/60 mb-4 font-medium uppercase tracking-widest">Other Scored Tools</h3>
          <div className="grid grid-cols-3 gap-4">
            {alternatives.map((tool: any, index: number) => (
              <motion.div
                key={tool.Tool}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.8 + index * 0.1 }}
                className="p-4 rounded-lg bg-white/5 border border-white/5 hover:border-[var(--electric-violet)]/40 transition-all duration-300 cursor-default"
              >
                <div className="text-sm text-white mb-1 uppercase font-mono">{tool.Tool}</div>
                <div className="text-xl text-[var(--neon-green)] mb-2 font-mono">
                  {typeof tool["Overall Score"] === "number" ? tool["Overall Score"].toFixed(1) : "—"}
                </div>
                <div className="text-[10px] text-white/40 uppercase">IQSE Overall</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
