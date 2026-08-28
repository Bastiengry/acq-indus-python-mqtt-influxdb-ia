interface FanMetricCardProps {
  id: string;
  label: string;
  value: number | null | undefined;
  unit: string;
  decimals: number;
  color: string;
  isFaulty: boolean;
}

export default function FanMetricCard({ label, value, unit, decimals, color, isFaulty }: FanMetricCardProps) {
  const cardStyle = isFaulty
    ? "bg-red-950/40 border-red-500 animate-pulse shadow-lg shadow-red-900/20"
    : "bg-slate-800/40 border-slate-800 hover:border-slate-700";

  return (
    <div className={`p-4 rounded-xl border transition-all duration-300 ${cardStyle}`}>
      <div className="text-slate-400 text-xs uppercase tracking-widest mb-1 flex justify-between items-center">
        <span>{label}</span>
        {isFaulty && (
          <span className="text-[10px] text-center text-red-400 bg-red-900/80 border border-red-700 px-2 py-0.5 rounded font-bold font-mono leading-tight">
            ANOMALIE<br />(z-score)
          </span>
        )}
      </div>
      <div className="text-3xl font-semibold font-mono tracking-tight" style={{ color }}>
        {value != null ? value.toFixed(decimals) : '--'} 
        <span className="text-sm font-normal text-slate-500 ml-1.5">{unit}</span>
      </div>
    </div>
  );
}