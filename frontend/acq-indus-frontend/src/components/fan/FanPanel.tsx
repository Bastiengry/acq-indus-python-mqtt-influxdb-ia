import { useState, useEffect } from 'react';
import Scene from './fan3d/FanScene';
import FanDataChart from './FanDataChart';
import FanDataCards from './FanDataCards';
import type { PredictionRecord } from '../../types/PredictionRecord';
import type { MeasureRecord } from '../../types/MeasureRecord';

interface FanProps { sensorId?: string; label?: string };


export default function FanPanel({ sensorId = 'UNKNOWN', label = 'UNKNOWN' }: FanProps) {
  const [measures, setMeasures] = useState<MeasureRecord[]>([]);
  const [prediction, setPrediction] = useState<PredictionRecord>();

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      if (sensorId === 'UNKNOWN') return;

      try {
        const [dataRes, predRes] = await Promise.all([
          fetch(`/ai-api/last-data/${sensorId}`),
          fetch(`/ai-api/last-prediction/${sensorId}`)
        ]);

        const measData: MeasureRecord[] = dataRes.ok ? await dataRes.json() : {};
        const predData: PredictionRecord = predRes.ok ? await predRes.json() : {};

        if (!isMounted) return;

        // Mise à jour des historiques dans le state
        setMeasures(measData);
        setPrediction(predData);

      } catch (error) {
        console.error("Erreur de récupération des données et prédictions :", error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [sensorId]);

  return (
    <div className="flex flex-col md:flex-row w-full max-w-full h-auto md:h-screen bg-slate-950 text-white font-sans overflow-x-hidden overflow-y-auto md:overflow-y-hidden">
      
      {/* 1. Vue 3D */}
      <div className="w-full md:w-[60%] h-[300px] md:h-full relative overflow-hidden min-w-0 flex-1">
        <div className="absolute top-4 left-4 z-10 pointer-events-none">
          <h1 className="text-2xl md:text-4xl font-bold tracking-tighter italic">
            {label !== 'UNKNOWN' ? label : sensorId}
          </h1>
          <p className={`text-sm md:text-xl font-mono ${
            prediction?.health_status === 'CRITICAL' ? 'text-red-500 animate-pulse' : 'text-emerald-400'
          }`}>
            STATUT : {prediction?.health_status}
          </p>
        </div>

        <Scene healthStatus={prediction?.health_status} vibration={prediction?.last_vibration} />
      </div>

      {/* 2. Panneau latéral de métriques */}
      <div className="w-full md:w-[40%] h-auto md:h-full bg-slate-900 md:border-l border-t md:border-t-0 border-slate-800 p-4 md:p-6 flex flex-col gap-4 md:gap-6 overflow-y-auto min-w-0">
        <FanDataCards 
          vibration={prediction?.last_vibration} 
          temperature={prediction?.last_temperature} 
          current={prediction?.last_current} 
          faultyFeature={prediction?.faulty_feature}
        />
        
        <FanDataChart 
          measures={measures}
        />
        
        <div className="mt-auto p-3 bg-slate-950 rounded-lg text-slate-400 font-mono text-xs border border-slate-800 space-y-1">
          <div>SYSTEM_LOG: Monitoring actif ({measures.length} mesures)</div>
          <div className="text-slate-300">
            DIAGNOSTIC: <span className={prediction?.health_status === 'CRITICAL' ? 'text-red-400 font-bold' : 'text-emerald-400'}>
              {prediction?.ai_message ||'Aucun diagnostic disponible'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}