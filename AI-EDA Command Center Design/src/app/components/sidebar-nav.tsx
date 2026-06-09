import { motion } from "motion/react";
import { Microscope, Sparkles, Layers, CheckSquare, Square, Zap } from "lucide-react";

interface SidebarNavProps {
  selectedTools: string[];
  onToggleTool: (tool: string) => void;
}

const edaTools = [
  { id: "ydata", name: "ydata-profiling" },
  { id: "sweetviz", name: "Sweetviz" },
  { id: "autoviz", name: "AutoViz" },
  { id: "lux", name: "Lux" },
];

export function SidebarNav({ selectedTools, onToggleTool }: SidebarNavProps) {
  return (
    <motion.aside
      initial={{ x: -300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="w-72 h-screen backdrop-blur-xl bg-[var(--deep-space-blue)]/80 border-r border-[var(--electric-violet)]/30 p-6 overflow-y-auto"
    >
      {/* Logo Area */}
      <div className="mb-8">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="flex items-center gap-3 mb-2"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--electric-violet)] to-[var(--cyber-cyan)] flex items-center justify-center shadow-[0_0_24px_rgba(139,92,246,0.4)]">
            <Microscope className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-display font-bold bg-gradient-to-r from-[var(--electric-violet)] to-[var(--cyber-cyan)] bg-clip-text text-transparent">
              AI-EDA Audit
            </h1>
            <p className="text-xs text-white/50 font-mono tracking-wider">Command Center</p>
          </div>
        </motion.div>
      </div>

      {/* Tool Selector */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm uppercase tracking-wider text-white/60">EDA Tools</h3>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[var(--electric-violet)]/20 text-[var(--electric-violet)] border border-[var(--electric-violet)]/30">
            {selectedTools.length} active
          </span>
        </div>
        <div className="space-y-3">
          {edaTools.map((tool, index) => {
            const active = selectedTools.includes(tool.id);
            return (
              <motion.div
                key={tool.id}
                initial={{ x: -50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                whileHover={{ x: 4, transition: { duration: 0.2 } }}
                className="group"
              >
                <button
                  onClick={() => onToggleTool(tool.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg backdrop-blur-sm border transition-all duration-300 ${
                    active
                      ? "bg-[var(--electric-violet)]/15 border-[var(--electric-violet)]/40 shadow-[0_0_18px_rgba(139,92,246,0.18)]"
                      : "bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/10"
                  }`}
                >
                  {active ? (
                    <CheckSquare className="w-5 h-5 text-[var(--neon-green)]" />
                  ) : (
                    <Square className="w-5 h-5 text-white/30" />
                  )}
                  <span className={`text-sm ${active ? "text-white" : "text-white/60"}`}>{tool.name}</span>
                </button>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* System panel */}
      <div className="space-y-4">
        <h3 className="text-sm uppercase tracking-wider text-white/60 mb-4">System</h3>

        {/* AI Engine */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="p-4 rounded-lg backdrop-blur-sm bg-gradient-to-br from-[var(--electric-violet)]/15 to-transparent border border-[var(--electric-violet)]/25"
        >
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-[var(--electric-violet)]" />
            <span className="text-xs text-white/60">AI Engine</span>
          </div>
          <div className="text-base font-mono text-white">Groq · Llama 3.3</div>
          <div className="text-[10px] text-white/40 font-mono mt-1">70B · sub-second inference</div>
        </motion.div>

        {/* Pipeline capabilities */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="p-4 rounded-lg backdrop-blur-sm bg-white/5 border border-white/10"
        >
          <div className="flex items-center gap-2 mb-3">
            <Layers className="w-4 h-4 text-[var(--neon-green)]" />
            <span className="text-xs text-white/60">Pipeline</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-white/70">
            <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-[var(--cyber-cyan)]" /> Profiling</span>
            <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-[var(--cyber-cyan)]" /> IQSE Scoring</span>
            <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-[var(--cyber-cyan)]" /> Gap Detect</span>
            <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-[var(--cyber-cyan)]" /> Reliability</span>
          </div>
        </motion.div>

        <p className="text-[10px] text-white/30 font-mono text-center pt-2 leading-relaxed">
          FastAPI · React · Groq AI<br />Benchmarking 4 EDA engines
        </p>
      </div>
    </motion.aside>
  );
}
