export interface TelemetryPoint {
  vibration: number;
  temperature: number;
  current: number;
  faulty_feature: string | null;
  fault_label: string | null;
  ai_message: string;
  health_status: 'OK' | 'WARNING' | 'CRITICAL';
}