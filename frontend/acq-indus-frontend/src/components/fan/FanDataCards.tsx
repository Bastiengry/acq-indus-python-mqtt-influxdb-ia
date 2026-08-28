import { METRIC_COLORS } from "./FanConstants";
import FanMetricCard from "./FanMetricCard";

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

  // Configuration déclarative des métriques
  const metrics = [
    {
      id: "vibration",
      label: "Vibration",
      value: vibration,
      unit: "mm/s",
      decimals: 2,
      color: METRIC_COLORS.vibration,
    },
    {
      id: "temperature",
      label: "Température",
      value: temperature,
      unit: "°C",
      decimals: 1,
      color: METRIC_COLORS.temperature,
    },
    {
      id: "current",
      label: "Courant",
      value: current,
      unit: "A",
      decimals: 1,
      color: METRIC_COLORS.current,
    },
  ];

  return (
    <div className="space-y-4">
      <div>
        <p className="text-slate-500 text-xs font-semibold tracking-wider uppercase mb-3">
          Dernières valeurs d'évaluation d'anomalie
        </p>
        
        {/* 'grid-cols-1' empile proprement les cartes dans la sidebar sans surcharger l'espace horizontal */}
        <div className="grid grid-cols-1 gap-3">
          {metrics.map((metric) => (
            <FanMetricCard
              key={metric.id}
              {...metric}
              isFaulty={faultyFeature === metric.id}
            />
          ))}
        </div>
      </div>

      <p className="text-orange-400 text-xs italic leading-relaxed bg-slate-950/50 p-3 rounded-lg border border-slate-800/50">
        Évaluation cyclique de l'anomalie par <strong className="text-slate-400">Isolation Forest</strong>.<br />
        Uniquement en cas d'anomalie, un calcul de <strong className="text-slate-400">Z-score</strong> isole la variable responsable (badge rouge sur la Card correspondante).
      </p>
    </div>
  );
}