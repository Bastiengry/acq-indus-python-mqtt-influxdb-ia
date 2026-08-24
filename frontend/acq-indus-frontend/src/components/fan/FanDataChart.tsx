import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { MeasureRecord } from '../../types/MeasureRecord';
import { METRIC_COLORS } from './FanConstants';

interface DataChartProps {
  measures: MeasureRecord[];
}

export default function DataChart({ measures }: DataChartProps) {
  // Fonction pour afficher uniquement l'heure (ex: 09:56:55)
  const formatTime = (timeStr: string) => {
    if (!timeStr) return '';
    try {
      const date = new Date(timeStr);
      return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return timeStr;
    }
  };

  return (
    <div className="bg-slate-800 p-4 rounded-lg shadow-inner w-full flex flex-col">
      <h3 className="text-slate-400 text-sm font-semibold mb-4 uppercase tracking-wider">
        Données en temps réel
      </h3>
      
      <div style={{ width: '100%', height: '250px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={measures}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis 
              dataKey="timestamp"
              tickFormatter={formatTime}
              stroke="#94a3b8" 
              fontSize={10}
              tick={{ fill: '#94a3b8' }}
              interval="preserveStartEnd"
              minTickGap={20}
            />
            <YAxis 
              domain={['auto', 'auto']}
              stroke="#94a3b8" 
              fontSize={10} 
              tickCount={6}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
              labelFormatter={(label) => formatTime(String(label ?? ''))}
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