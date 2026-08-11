import { METRIC_COLORS } from "./Constants";

interface DataCardsProps {
  currentVibration: number | null;
  currentTemperature: number | null;
  currentCurrent: number | null;
  faultyFeature?: string | null; // "vibration", "temperature", "current" ou null
}

export default function DataCards({ 
  currentVibration, 
  currentTemperature, 
  currentCurrent,
  faultyFeature 
}: DataCardsProps) {

  // Fonction helper pour déterminer le style de bordure et de fond selon l'anomalie
  const getCardStyle = (metricName: string) => {
    const isFaulty = faultyFeature === metricName;
    
    if (isFaulty) {
      return "bg-red-950/30 border-red-500 animate-pulse shadow-lg shadow-red-900/20";
    }
    
    return "bg-slate-800/50 border-slate-700";
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Carte Vibration */}
      <div className={`p-6 rounded-2xl border transition-all duration-300 ${getCardStyle("vibration")}`}>
        <p className="text-slate-400 text-xs uppercase tracking-widest mb-1 flex justify-between items-center">
          <span>Vibration</span>
          {faultyFeature === "vibration" && (
            <span className="text-[10px] text-red-400 bg-red-900/50 px-2 py-0.5 rounded font-bold">
              ANOMALIE
            </span>
          )}
        </p>
        <p className="text-5xl font-light" style={{ color: METRIC_COLORS.vibration }}>
          {currentVibration != null ? currentVibration.toFixed(2) : '--'} 
          <span className="text-lg text-slate-500 ml-1">mm/s</span>
        </p>
      </div>

      {/* Carte Température */}
      <div className={`p-6 rounded-2xl border transition-all duration-300 ${getCardStyle("temperature")}`}>
        <p className="text-slate-400 text-xs uppercase tracking-widest mb-1 flex justify-between items-center">
          <span>Température</span>
          {faultyFeature === "temperature" && (
            <span className="text-[10px] text-red-400 bg-red-900/50 px-2 py-0.5 rounded font-bold">
              ANOMALIE
            </span>
          )}
        </p>
        <p className="text-5xl font-light" style={{ color: METRIC_COLORS.temperature }}>
          {currentTemperature != null ? currentTemperature.toFixed(1) : '--'} 
          <span className="text-lg text-slate-500 ml-1">°C</span>
        </p>
      </div>

      {/* Carte Courant */}
      <div className={`p-6 rounded-2xl border transition-all duration-300 ${getCardStyle("current")}`}>
        <p className="text-slate-400 text-xs uppercase tracking-widest mb-1 flex justify-between items-center">
          <span>Courant</span>
          {faultyFeature === "current" && (
            <span className="text-[10px] text-red-400 bg-red-900/50 px-2 py-0.5 rounded font-bold">
              ANOMALIE
            </span>
          )}
        </p>
        <p className="text-5xl font-light" style={{ color: METRIC_COLORS.current }}>
          {currentCurrent != null ? currentCurrent.toFixed(1) : '--'} 
          <span className="text-lg text-slate-500 ml-1">A</span>
        </p>
      </div>
    </div>
  );
}