import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface VibrationChartProps {
  currentVibe: number;
}

interface DataPoint {
  time: string;
  value: number;
}

export default function VibrationChart({ currentVibe }: VibrationChartProps) {
  const [data, setData] = useState<DataPoint[]>([]);

  const [prevVibe, setPrevVibe] = useState<number>(currentVibe);

  // TECHNIQUE : On synchronise l'état directement si la prop change
  // C'est la méthode recommandée pour éviter les useEffect en cascade
  if (currentVibe !== prevVibe) {
    setPrevVibe(currentVibe);
    const now = new Date();
    const timeStr = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;
    
    setData(prev => {
      const next = [...prev, { time: timeStr, value: currentVibe }];
      return next.slice(-20); 
    });
  }

  return (
    <div className="bg-slate-800 p-4 rounded-lg shadow-inner w-full flex flex-col">
        <h3 className="text-slate-400 text-sm font-semibold mb-4 uppercase tracking-wider">
        Vibration (mm/s)
        </h3>
        
        {/* On force la hauteur ici pour que Recharts "existe" */}
        <div style={{ width: '100%', height: '250px' }}>
        <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis 
                dataKey="time" 
                stroke="#94a3b8" 
                fontSize={10}
                tick={{fill: '#94a3b8'}}
                interval="preserveStartEnd" // Évite que les labels se chevauchent
                minTickGap={20} // Espace minimum entre deux heures affichées
            />
            <YAxis 
                domain={[0, 10]} 
                stroke="#94a3b8" 
                fontSize={10} 
                tickCount={6}
            />
            <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
            />
            <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#38bdf8" 
                strokeWidth={2} 
                dot={false}
                isAnimationActive={false}
            />
            </LineChart>
        </ResponsiveContainer>
        </div>
    </div>
    );
}