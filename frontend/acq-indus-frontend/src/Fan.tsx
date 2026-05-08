import { useState, useEffect } from 'react';
import Scene from './components/Three/Scene';
import VibrationChart from './components/Dashboard/VibrationChart';

export default function Fan() {
  const [telemetry, setTelemetry] = useState({
    vibration: 0,
    health_status: 'OK'
  });

 useEffect(() => {
    // Fonction pour récupérer les données du "Cerveau" (FastAPI)
    const fetchData = async () => {
      try {
        const response = await fetch('/ai-api/health/TUNNEL_NORD_01');
        const data = await response.json();
        setTelemetry({
          vibration: data.last_vibration || 0, 
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
          <h1 className="text-4xl font-bold tracking-tighter italic">TUNNEL NORTH - FAN 01</h1>
          <p className={`text-xl font-mono ${telemetry.health_status === 'CRITICAL' ? 'text-red-500 animate-pulse' : 'text-emerald-400'}`}>
            STATUT : {telemetry.health_status}
          </p>
        </div>
        <Scene healthStatus={telemetry.health_status} vibration={telemetry.vibration} />
      </div>

      {/* Côté droit : Le Dashboard */}
      <div className="w-200 bg-slate-900 border-l border-slate-800 p-6 flex flex-col gap-6">
        <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700">
          <p className="text-slate-400 text-xs uppercase tracking-widest mb-1">Vibration Actuelle</p>
          <p className="text-5xl font-light text-cyan-400">{telemetry.vibration?.toFixed(2)} <span className="text-lg text-slate-500">mm/s</span></p>
        </div>
        
        <VibrationChart currentVibe={telemetry.vibration} />
        
        <div className="mt-auto p-4 bg-slate-950 rounded-lg text-white text-slate-600 font-mono">
          SYSTEM_LOG: Monitoring active... <br/>
          AI_MODEL: ISO-10816 Analysis <br/>
          SOCKET_PORT: 8000
        </div>
      </div>
    </div>
  );
}