import { METRIC_COLORS } from "./FanConstants";

interface DataCardsProps {
  vibration: number | null | undefined;
  temperature: number | null | undefined;
  current: number | null | undefined;
  faultyFeature?: string | null;
}

export default function DataCards({ 
  vibration, 
  temperature, 
  current,
  faultyFeature 
}: DataCardsProps) {

  const getCardStyle = (metricName: string) => {
    const isFaulty = faultyFeature === metricName;
    
    if (isFaulty) {
      return "bg-red-950/40 border-red-500 animate-pulse shadow-lg shadow-red-900/20";
    }
    
    return "bg-slate-800/40 border-slate-800 hover:border-slate-700";
  };

  return (
    // 'grid-cols-1' force les cartes à s'empiler proprement dans la sidebar
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Carte Vibration */}
      <div className={`p-4 rounded-xl border transition-all duration-300 ${getCardStyle("vibration")}`}>
        <div className="text-slate-400 text-xs uppercase tracking-widest mb-1 flex justify-between items-center">
          <span>Vibration</span>
          {faultyFeature === "vibration" && (
            <span className="text-[10px] text-red-400 bg-red-900/60 px-2 py-0.5 rounded font-bold font-mono">
              ANOMALIE
            </span>
          )}
        </div>
        <div className="text-3xl font-semibold font-mono tracking-tight" style={{ color: METRIC_COLORS.vibration }}>
          {vibration != null ? vibration.toFixed(2) : '--'} 
          <span className="text-sm font-normal text-slate-500 ml-1.5">mm/s</span>
        </div>
      </div>

      {/* Carte Température */}
      <div className={`p-4 rounded-xl border transition-all duration-300 ${getCardStyle("temperature")}`}>
        <div className="text-slate-400 text-xs uppercase tracking-widest mb-1 flex justify-between items-center">
          <span>Température</span>
          {faultyFeature === "temperature" && (
            <span className="text-[10px] text-red-400 bg-red-900/60 px-2 py-0.5 rounded font-bold font-mono">
              ANOMALIE
            </span>
          )}
        </div>
        <div className="text-3xl font-semibold font-mono tracking-tight" style={{ color: METRIC_COLORS.temperature }}>
          {temperature != null ? temperature.toFixed(1) : '--'} 
          <span className="text-sm font-normal text-slate-500 ml-1.5">°C</span>
        </div>
      </div>

      {/* Carte Courant */}
      <div className={`p-4 rounded-xl border transition-all duration-300 ${getCardStyle("current")}`}>
        <div className="text-slate-400 text-xs uppercase tracking-widest mb-1 flex justify-between items-center">
          <span>Courant</span>
          {faultyFeature === "current" && (
            <span className="text-[10px] text-red-400 bg-red-900/60 px-2 py-0.5 rounded font-bold font-mono">
              ANOMALIE
            </span>
          )}
        </div>
        <div className="text-3xl font-semibold font-mono tracking-tight" style={{ color: METRIC_COLORS.current }}>
          {current != null ? current.toFixed(1) : '--'} 
          <span className="text-sm font-normal text-slate-500 ml-1.5">A</span>
        </div>
      </div>
    </div>
  );
}