import { useState, useEffect } from 'react';
import Scene from './components/Three/Scene';
import DataChart from './components/Dashboard/DataChart';
import DataCards from './components/Dashboard/DataCards';

type FanProps = { sensorId?: string; label?: string };

export default function Fan({ sensorId = 'UNKNOWN', label = 'UNKNOWN' }: FanProps) {
  const [telemetry, setTelemetry] = useState({
    vibration: 0,
    temperature: 0,
    current: 0,
    faulty_feature: null,
    health_status: 'OK'
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/ai-api/data-with-anomaly-detection/${sensorId}`);
        const data = await response.json();
        setTelemetry({
          vibration: data.last_vibration || 0, 
          temperature: data.last_temperature || 0, 
          current: data.last_current || 0, 
          faulty_feature: data.faulty_feature || null,
          health_status: data.health_status || 'OK'
        });
      } catch (error) {
        console.error("Erreur de connexion à l'IA:", error);
      }
    };

    const interval = setInterval(fetchData, 1000);
    fetchData();
    return () => clearInterval(interval);
  }, [sensorId]);

  return (
    // max-w-full + overflow-x-hidden bloquent le scroll horizontal au niveau racine
    <div className="flex flex-col md:flex-row w-full max-w-full h-auto md:h-screen bg-slate-950 text-white font-sans overflow-x-hidden overflow-y-auto md:overflow-y-hidden">
      
      {/* 1. Zone 3D : min-w-0 autorise le conteneur à rétrécir sous les 100% sans forcer le parent */}
      <div className="w-full md:w-[60%] h-[300px] md:h-full relative overflow-hidden min-w-0 flex-1">
        <div className="absolute top-4 left-4 z-10 pointer-events-none">
          <h1 className="text-2xl md:text-4xl font-bold tracking-tighter italic">{label ?? sensorId ?? 'UNKNOWN'}</h1>
          <p className={`text-sm md:text-xl font-mono ${telemetry.health_status === 'CRITICAL' ? 'text-red-500 animate-pulse' : 'text-emerald-400'}`}>
            STATUT : {telemetry.health_status}
          </p>
        </div>

        <Scene healthStatus={telemetry.health_status} vibration={telemetry.vibration} />
      </div>

      {/* 2. Panneau latéral : min-w-0 résout le bug de débordement Recharts / DataCards */}
      <div className="w-full md:w-[40%] h-auto md:h-full bg-slate-900 md:border-l border-t md:border-t-0 border-slate-800 p-4 md:p-6 flex flex-col gap-4 md:gap-6 overflow-y-auto min-w-0">
        <DataCards 
          currentVibration={telemetry.vibration} 
          currentTemperature={telemetry.temperature} 
          currentCurrent={telemetry.current} 
          faultyFeature={telemetry?.faulty_feature}
        />
        
        <DataChart 
          currentVibration={telemetry.vibration} 
          currentTemperature={telemetry.temperature} 
          currentCurrent={telemetry.current}
          sensorId={sensorId}
        />
        
        <div className="mt-auto p-3 bg-slate-950 rounded-lg text-slate-400 font-mono text-xs border border-slate-800">
          SYSTEM_LOG: Monitoring active... <br/>
          AI_MODEL: ISO-10816 Analysis <br/>
          SOCKET_PORT: 8000
        </div>
      </div>
    </div>
  );
}