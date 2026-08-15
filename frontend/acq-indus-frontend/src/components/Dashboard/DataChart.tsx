import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { METRIC_COLORS } from './Constants';

interface DataChartProps {
  sensorId: string;
  currentVibration: number;
  currentTemperature: number;
  currentCurrent: number;
}

interface DataPoint {
  time: string;
  vibration: number;
  temperature: number;
  current: number;
}

export default function DataChart({ sensorId, currentVibration, currentTemperature, currentCurrent }: DataChartProps) {
  const [data, setData] = useState<DataPoint[]>([]);
  const [prevSensorId, setPrevSensorId] = useState<string>(sensorId);
  const [prevVibration, setPrevVibration] = useState<number>(currentVibration);
  const [prevTemperature, setPrevTemperature] = useState<number>(currentTemperature);
  const [prevCurrent, setPrevCurrent] = useState<number>(currentCurrent);

  if (currentVibration !== prevVibration) {
    setPrevVibration(currentVibration);
  }

  if (currentTemperature !== prevTemperature) {
    setPrevTemperature(currentTemperature);
  }

  if (currentCurrent !== prevCurrent) {
    setPrevCurrent(currentCurrent);
  }

  if (currentVibration !== prevVibration || currentTemperature !== prevTemperature || currentCurrent !== prevCurrent) {
    const now = new Date();
    const timeStr = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;
    if (sensorId === prevSensorId) {
      setData(prev => {
        const next = [...prev, { time: timeStr, vibration: currentVibration, temperature: currentTemperature, current: currentCurrent }];
        return next.slice(-20); 
      });
    } else {
      setPrevSensorId(sensorId);
      setData([ { time: timeStr, vibration: currentVibration, temperature: currentTemperature, current: currentCurrent }]);
    }
  }

  return (
    <div className="bg-slate-800 p-4 rounded-lg shadow-inner w-full flex flex-col">
        <h3 className="text-slate-400 text-sm font-semibold mb-4 uppercase tracking-wider">
        Données en temps réel
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
                dataKey="vibration" 
                stroke={METRIC_COLORS.vibration}
                strokeWidth={2} 
                dot={false}
                isAnimationActive={false}
            />
            <Line 
                type="monotone" 
                dataKey="temperature" 
                stroke={METRIC_COLORS.temperature}
                strokeWidth={2} 
                dot={false}
                isAnimationActive={false}
            />
            <Line 
                type="monotone" 
                dataKey="current" 
                stroke={METRIC_COLORS.current}
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