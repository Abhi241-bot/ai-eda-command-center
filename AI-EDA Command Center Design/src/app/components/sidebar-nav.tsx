import { motion } from "motion/react";
import { Microscope, Clock, Cpu, CheckSquare, Square } from "lucide-react";
import { Progress } from "./ui/progress";

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
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[var(--electric-violet)] to-[var(--neon-green)] flex items-center justify-center">
            <Microscope className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-[var(--electric-violet)] to-[var(--neon-green)] bg-clip-text text-transparent">
              AI-EDA Audit
            </h1>
            <p className="text-xs text-white/60">Command Center</p>
          </div>
        </motion.div>
      </div>

      {/* Tool Selector */}
      <div className="mb-8">
        <h3 className="text-sm uppercase tracking-wider text-white/60 mb-4">
          EDA Tools
        </h3>
        <div className="space-y-3">
          {edaTools.map((tool, index) => (
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
                className="w-full flex items-center gap-3 p-3 rounded-lg backdrop-blur-sm bg-white/5 border border-white/10 hover:border-[var(--electric-violet)]/50 hover:bg-white/10 transition-all duration-300"
              >
                {selectedTools.includes(tool.id) ? (
                  <CheckSquare className="w-5 h-5 text-[var(--neon-green)]" />
                ) : (
                  <Square className="w-5 h-5 text-white/40" />
                )}
                <span className="text-white/90 text-sm">{tool.name}</span>
              </button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Quick Metrics */}
      <div className="space-y-4">
        <h3 className="text-sm uppercase tracking-wider text-white/60 mb-4">
          Quick Metrics
        </h3>

        {/* Last Run Duration */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="p-4 rounded-lg backdrop-blur-sm bg-white/5 border border-white/10"
        >
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-[var(--electric-violet)]" />
            <span className="text-xs text-white/60">Last Run Duration</span>
          </div>
          <div className="text-2xl font-mono text-white">2.4s</div>
          <div className="mt-3">
            <Progress value={65} className="h-1.5" />
          </div>
        </motion.div>

        {/* Memory Efficiency */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="p-4 rounded-lg backdrop-blur-sm bg-white/5 border border-white/10"
        >
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="w-4 h-4 text-[var(--neon-green)]" />
            <span className="text-xs text-white/60">Memory Efficiency</span>
          </div>
          <div className="text-2xl font-mono text-white">94%</div>
          <div className="mt-3">
            <Progress value={94} className="h-1.5" />
          </div>
        </motion.div>
      </div>
    </motion.aside>
  );
}
