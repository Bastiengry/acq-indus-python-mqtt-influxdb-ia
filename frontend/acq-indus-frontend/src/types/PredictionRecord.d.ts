export interface PredictionRecord {
  timestamp?: string;
  fan_id: string;
  health_status: 'OK' | 'WARNING' | 'CRITICAL';
  faulty_feature: string | null;
  fault_label: string | null;
  ai_message: string;
  last_vibration: number;
  last_temperature: number;
  last_current: number;
};