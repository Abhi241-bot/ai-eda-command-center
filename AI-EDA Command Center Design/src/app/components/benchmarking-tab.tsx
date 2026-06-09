import { motion } from "motion/react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Trophy, TrendingUp, Award, BarChart3 } from "lucide-react";

interface BenchmarkingTabProps {
  data: any; // benchmarking results
  scores?: any; // IQSE scores
}

interface RadarDataItem {
  metric: string;
  [key: string]: string | number;
}

export function BenchmarkingTab({ data, scores }: BenchmarkingTabProps) {
  // Convert benchmarking data to radar format
  // metrics: Correctness (from IQSE), Relevance (from IQSE), Speed (from Benchmark), Memory (from Benchmark)
  
  const tools = data ? Object.keys(data) : [];
  
  const radarData: RadarDataItem[] = [
    { metric: "Correctness" },
    { metric: "Relevance" },
    { metric: "Coverage" },
    { metric: "Speed (Inv)" },
    { metric: "Memory (Inv)" },
  ];

  if (data && scores) {
    tools.forEach(tool => {
      const toolScores = scores[tool] || { correctness: 5, relevance: 5, coverage: 5 };
      const toolBench = data[tool] || { duration_sec: 10, memory_delta_mb: 100 };
      
      // We invert speed and memory for the radar (higher is better)
      radarData[0][tool] = (toolScores.correctness || 0) * 10;
      radarData[1][tool] = (toolScores.relevance || 0) * 10;
      radarData[2][tool] = (toolScores.coverage || 0) * 10;
      radarData[3][tool] = Math.max(0, 100 - ((toolBench.duration_sec || 10) * 5));
      radarData[4][tool] = Math.max(0, 100 - ((toolBench.memory_delta_mb || 100) / 2));
    });
  }

  // Leaderboard from IQSE scores
  const leaderboard = scores ? Object.entries(scores)
    .map(([tool, s]: [string, any]) => ({
      tool,
      score: ((s.correctness + s.relevance + s.coverage) / 3 * 10).toFixed(1),
      correctness: s.correctness * 10,
      relevance: s.relevance * 10,
      coverage: s.coverage * 10,
    }))
    .sort((a, b) => Number(b.score) - Number(a.score))
    .map((item, i) => ({ ...item, rank: i + 1 }))
    : [];

  const rankColors = ["#FFD700", "#C0C0C0", "#CD7F32", "#8B7355"];
  const toolColors = ["var(--electric-violet)", "var(--neon-green)", "var(--soft-coral)", "#f59e0b"];

  return (
    <div className="space-y-6">
      {!data ? (
        <div className="glass p-20 flex flex-col items-center justify-center text-white/30 rounded-2xl gap-4">
          <BarChart3 className="w-16 h-16 text-[var(--electric-violet)]/30 animate-float" />
          <p className="font-mono text-sm uppercase tracking-wider">No benchmarking data — run analysis in the Data Hub</p>
        </div>
      ) : (
        <>
          {/* Radar Chart */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="p-6 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10"
          >
            <div className="flex items-center gap-2 mb-6">
              <TrendingUp className="w-5 h-5 text-[var(--electric-violet)]" />
              <h3 className="text-lg text-white">Performance Multi-Metric Comparison</h3>
            </div>

            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.4)' }} />
                {tools.map((tool, i) => (
                  <Radar
                    key={tool}
                    name={tool}
                    dataKey={tool}
                    stroke={toolColors[i % toolColors.length]}
                    fill={toolColors[i % toolColors.length]}
                    fillOpacity={0.4}
                    strokeWidth={2}
                  />
                ))}
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 12, 41, 0.9)',
                    border: '1px solid rgba(118, 75, 162, 0.3)',
                    borderRadius: '8px',
                    color: 'white',
                  }}
                />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Leaderboard */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="p-6 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10"
          >
            <div className="flex items-center gap-2 mb-6">
              <Trophy className="w-5 h-5 text-[#FFD700]" />
              <h3 className="text-lg text-white">IQSE Tool Leaderboard</h3>
              <span className="text-xs text-white/60 ml-auto">Insight Quality Scoring Engine</span>
            </div>

            <div className="space-y-3">
              {leaderboard.map((item, index) => (
                <motion.div
                  key={item.tool}
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.01 }}
                  className="relative group"
                >
                  <div className="relative p-4 rounded-lg backdrop-blur-sm bg-white/5 border border-white/10 group-hover:border-white/30 transition-all duration-300">
                    <div className="flex items-center gap-4">
                      {/* Rank */}
                      <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center text-xl font-bold"
                        style={{ backgroundColor: `${rankColors[index] || '#ffffff20'}40`, color: rankColors[index] || '#fff' }}
                      >
                        {item.rank}
                      </div>

                      {/* Tool Name */}
                      <div className="flex-1">
                        <h4 className="text-white font-mono uppercase tracking-wider text-sm">{item.tool}</h4>
                        <div className="flex gap-4 mt-1 opacity-60">
                          <span className="text-[10px] text-white/80">Correctness: {item.correctness}</span>
                          <span className="text-[10px] text-white/80">Relevance: {item.relevance}</span>
                          <span className="text-[10px] text-white/80">Coverage: {item.coverage}</span>
                        </div>
                      </div>

                      {/* Score */}
                      <div className="text-right">
                        <div className="text-2xl font-mono text-white">{item.score}</div>
                        <div className="text-[10px] text-white/40 uppercase">IQSE</div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mt-3 h-1 bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${item.score}%` }}
                        className="h-full bg-gradient-to-r from-[var(--electric-violet)] to-[var(--neon-green)]"
                      />
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
}
