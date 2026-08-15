import { useState, useEffect } from 'react';
import Scene from './components/Three/Scene';
import DataChart from './components/Dashboard/DataChart';
import DataCards from './components/Dashboard/DataCards';

export default function Fan() {
  const [telemetry, setTelemetry] = useState({
    vibration: 0,
    temperature: 0,
    current: 0,
    faulty_feature: null,
    health_status: 'OK'
  });

 useEffect(() => {
    // Fonction pour récupérer les données du "Cerveau" (FastAPI)
    const fetchData = async () => {
      try {
        const response = await fetch('/ai-api/data-with-anomaly-detection/FAN_01');
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

    // On poll l'API toutes les secondes pour le temps réel
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen bg-slate-950 text-white font-sans">
      {/* Côté gauche : La 3D */}
      <div className="flex-grow relative">
        <div className="absolute top-8 left-8 z-10 pointer-events-none">
          <h1 className="text-4xl font-bold tracking-tighter italic">FAN 01</h1>
          <p className={`text-xl font-mono ${telemetry.health_status === 'CRITICAL' ? 'text-red-500 animate-pulse' : 'text-emerald-400'}`}>
            STATUT : {telemetry.health_status}
          </p>
        </div>
        <Scene healthStatus={telemetry.health_status} vibration={telemetry.vibration} />
      </div>

      {/* Côté droit : Le Dashboard */}
      <div className="w-200 bg-slate-900 border-l border-slate-800 p-6 flex flex-col gap-6">
        <DataCards currentVibration={telemetry.vibration} currentTemperature={telemetry.temperature} currentCurrent={telemetry.current} faultyFeature={telemetry?.faulty_feature}/>
        
        <DataChart 
          currentVibration={telemetry.vibration} 
          currentTemperature={telemetry.temperature} 
          currentCurrent={telemetry.current}/>
        
        <div className="mt-auto p-4 bg-slate-950 rounded-lg text-white text-slate-600 font-mono">
          SYSTEM_LOG: Monitoring active... <br/>
          AI_MODEL: ISO-10816 Analysis <br/>
          SOCKET_PORT: 8000
        </div>
      </div>
    </div>
  );
}