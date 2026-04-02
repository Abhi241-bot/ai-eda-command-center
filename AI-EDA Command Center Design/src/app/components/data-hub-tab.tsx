import { motion } from "motion/react";
import { Upload, Database, AlertCircle, Activity, Play, Layers, Loader2 } from "lucide-react";
import { useRef } from "react";

interface DataHubTabProps {
  profile: any;
  onUpload: (file: File) => void;
  onRun: () => void;
  loading?: boolean;
}

export function DataHubTab({ profile, onUpload, onRun, loading }: DataHubTabProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const stats = [
    { label: "Observations", value: profile?.observations?.toLocaleString() || "—", icon: Database, color: "var(--electric-violet)" },
    { label: "Features", value: profile?.features || "—", icon: Layers, color: "var(--neon-green)" },
    { label: "Missing Cells", value: profile?.missing_cells?.toLocaleString() || "—", icon: AlertCircle, color: "var(--soft-coral)" },
    { label: "Health Score", value: profile ? `${profile.health_score}%` : "—", icon: Activity, color: "var(--neon-green)" },
  ];

  return (
    <div className="space-y-6">
      <input 
        type="file" 
        ref={fileInputRef} 
        className="hidden" 
        accept=".csv"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onUpload(file);
        }}
      />

      {/* Upload Zone */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="p-10 rounded-2xl border-2 border-dashed border-white/10 bg-white/5 backdrop-blur-sm hover:border-[var(--electric-violet)]/50 transition-all group flex flex-col items-center justify-center gap-4 cursor-pointer relative overflow-hidden"
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--electric-violet)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <div className="w-16 h-16 rounded-full bg-[var(--electric-violet)]/10 flex items-center justify-center group-hover:scale-110 transition-transform relative z-10">
          <Upload className="w-8 h-8 text-[var(--electric-violet)]" />
        </div>
        <div className="text-center relative z-10">
          <h3 className="text-xl text-white font-medium mb-1">
            {profile ? `Current Dataset: ${profile.file_name}` : "Upload Local Dataset"}
          </h3>
          <p className="text-white/40 text-sm">Drag and drop your CSV file or click to browse</p>
        </div>
      </motion.div>

      {/* Profile Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 + index * 0.1 }}
            className="p-6 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10 hover:border-white/20 transition-all"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-white/5">
                <stat.icon className="w-5 h-5" style={{ color: stat.color }} />
              </div>
              <span className="text-xs text-white/60 uppercase tracking-wider font-medium">{stat.label}</span>
            </div>
            <div className="text-2xl font-mono text-white tracking-tight">{stat.value}</div>
          </motion.div>
        ))}
      </div>

      {/* Analysis Trigger - Only show when data is present */}
      {profile && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="p-8 rounded-2xl bg-gradient-to-br from-[var(--electric-violet)]/20 to-[var(--neon-green)]/20 border border-[var(--electric-violet)]/30 flex items-center justify-between shadow-2xl"
        >
          <div className="max-w-md">
            <h3 className="text-xl text-white mb-2 font-bold uppercase tracking-tight">Run System-Wide Analysis</h3>
            <p className="text-white/60 text-sm leading-relaxed">
              Execute all selected EDA tools, generate AI narratives, and detect insight gaps across your dataset.
            </p>
          </div>
          <button 
            onClick={onRun}
            disabled={loading}
            className="px-10 py-4 rounded-xl bg-gradient-to-r from-[var(--electric-violet)] to-[var(--neon-green)] text-white font-black tracking-widest flex items-center gap-3 hover:shadow-[0_0_40px_rgba(118,75,162,0.6)] transition-all disabled:opacity-50 disabled:cursor-not-allowed uppercase"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                ANALYZING...
              </>
            ) : (
              <>
                <Play className="w-5 h-5 fill-white" />
                START PIPELINE
              </>
            )}
          </button>
        </motion.div>
      )}

      {/* Data Preview */}
      {profile?.sample_data && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="p-6 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg text-white font-medium flex items-center gap-2">
                <Database className="w-5 h-5 text-[var(--electric-violet)]" />
                Sample Data Preview (Top 10)
            </h3>
            <span className="text-[10px] text-white/40 uppercase tracking-widest">Read-only Buffer</span>
          </div>
          <div className="overflow-x-auto rounded-lg border border-white/5">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-white/5 border-b border-white/10">
                  {Object.keys(profile.sample_data[0]).map((key) => (
                    <th key={key} className="py-4 px-4 text-white/60 font-mono font-bold uppercase tracking-wider">{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {profile.sample_data.map((row: any, i: number) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    {Object.values(row).map((val: any, j: number) => (
                      <td key={j} className="py-3 px-4 text-white/80 font-mono whitespace-nowrap">{String(val)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
}
