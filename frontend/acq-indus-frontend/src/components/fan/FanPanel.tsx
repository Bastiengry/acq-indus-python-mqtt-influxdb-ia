import { useState, useEffect } from 'react';
import FanScene from './fan3d/FanScene';
import FanDataChart from './FanDataChart';
import FanDataCards from './FanDataCards';
import type { PredictionRecord } from '../../types/PredictionRecord';
import type { MeasureRecord } from '../../types/MeasureRecord';

interface FanProps { 
  sensorId?: string; 
  label?: string;
}

export default function FanPanel({ sensorId = 'UNKNOWN', label = 'UNKNOWN' }: FanProps) {
  const [measures, setMeasures] = useState<MeasureRecord[]>([]);
  const [prediction, setPrediction] = useState<PredictionRecord>();

  useEffect(() => {
    if (sensorId === 'UNKNOWN') return;

    const controller = new AbortController();
    let isFetching = false;

    const fetchData = async () => {
      if (isFetching) return;
      isFetching = true;

      try {
        const [dataRes, predRes] = await Promise.all([
          fetch(`/ai-api/last-data/${sensorId}`, { signal: controller.signal }),
          fetch(`/ai-api/last-prediction/${sensorId}`, { signal: controller.signal })
        ]);

        const measData: MeasureRecord[] = dataRes.ok ? await dataRes.json() : [];
        const predData: PredictionRecord | undefined = predRes.ok ? await predRes.json() : undefined;

        setMeasures(Array.isArray(measData) ? measData : []);
        if (predData) setPrediction(predData);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } catch (error: any) {
        if (error.name !== 'AbortError') {
          console.error("Erreur de récupération des données et prédictions :", error);
        }
      } finally {
        isFetching = false;
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);

    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [sensorId]);

  const isCritical = prediction?.health_status === 'CRITICAL';

  return (
    <div className="flex flex-col md:flex-row w-full h-screen bg-slate-950 text-white font-sans overflow-hidden">
      
      {/* 1. Colonne principale (Header + 3D + Graphique) */}
      <div className="w-full md:w-[60%] h-full flex flex-col min-w-0">
        
        {/* HEADER */}
        <div className="p-3 bg-slate-950/80 border-b border-slate-800 space-y-1">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tighter italic">
            {label !== 'UNKNOWN' ? label : sensorId}
          </h1>
          <p className={`text-sm md:text-base font-mono ${
            isCritical ? 'text-red-500 animate-pulse' : 'text-emerald-400'
          }`}>
            STATUT <span className="text-orange-400">(ISOLATION FOREST)</span> : {prediction?.health_status ?? 'CHARGEMENT...'}
          </p>
        </div>

        {/* ZONE CENTRALE (3D) */}
        <div className="flex-1 w-full min-h-0">
          <FanScene healthStatus={prediction?.health_status} vibration={prediction?.last_vibration} />
        </div>

        {/* FOOTER (Graphique) */}
        <div className="bg-slate-900/50 border-t border-slate-800">
          <FanDataChart measures={measures} />
        </div>

      </div>

      {/* 2. Panneau latéral de métriques */}
      <div className="w-full md:w-[40%] h-full bg-slate-900 md:border-l border-t md:border-t-0 border-slate-800 p-4 md:p-6 flex flex-col gap-4 min-w-0 overflow-y-auto">
        <FanDataCards 
          vibration={prediction?.last_vibration} 
          temperature={prediction?.last_temperature} 
          current={prediction?.last_current} 
          faultyFeature={prediction?.faulty_feature}
        />
        
        <div className="mt-auto p-3 bg-slate-950 rounded-lg text-slate-400 font-mono text-xs border border-slate-800 space-y-1">
          <div>SYSTEM_LOG: Monitoring actif ({measures.length} mesures)</div>
          <div className="text-slate-300">
            DIAGNOSTIC : <span className={isCritical ? 'text-red-400 font-bold' : 'text-emerald-400'}>
              {prediction?.ml_message || 'Aucun diagnostic disponible'} <br/>
            </span>
          </div>

          <p className="text-xs m-3 italic text-orange-400 leading-relaxed bg-emerald-300 bg-gray-900 p-3 rounded-lg border border-slate-800/50">
            Le libellé du diagnostic est évalué grâce à RANDOM FOREST (classification).
          </p>
        </div>
      </div>

    </div>
  );
}