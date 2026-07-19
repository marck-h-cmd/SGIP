export interface DMA {
  id: number;
  code: string;
  name: string;
  district: string;
  latitude: number;
  longitude: number;
  status: string;
  population?: number;
  description?: string;
}

export interface Sensor {
  id: number;
  code: string;
  dma_id: string;
  name: string;
  type: 'PRESSURE' | 'FLOW';
  unit: string;
  status: string;
  latitude?: number;
  longitude?: number;
}

export interface TelemetryReading {
  id: number;
  timestamp: string;
  dma_id: string;
  sensor_id: string;
  pressure_mca: number;
  flow_lps: number;
  source: string;
  quality_flag: string;
  latitude?: number;
  longitude?: number;
}

export interface Anomaly {
  id: number;
  telemetry_id: number;
  dma_id: string;
  dma_name: string;
  sensor_id?: string;
  anomaly_score: number;
  severity: string;
  status: string;
  detected_at: string;
  pressure_variation?: number;
  flow_variation?: number;
  estimated_loss_volume?: number;
  description?: string;
}

export interface IncidentTicket {
  id: number;
  code: string;
  anomaly_id?: number;
  dma_id: string;
  dma_name: string;
  title: string;
  description?: string;
  priority: string;
  status: string;
  assigned_to?: string;
  sla_due_at?: string;
  created_at: string;
  resolved_at?: string;
  response_time_minutes?: number;
  resolution_time_minutes?: number;
}

export interface Alert {
  id: number;
  dma_id: string;
  dma_name: string;
  type: string;
  severity: string;
  message: string;
  acknowledged: boolean;
  created_at: string;
}

export interface KpiExecutive {
  total_dmas: number;
  active_incidents: number;
  critical_dmas: number;
  avg_detection_time_hours: number;
  water_loss_estimate_m3: number;
  sla_compliance: number;
  last_anomaly?: Anomaly;
}

export interface DmaMetrics {
  dma_id: string;
  dma_name: string;
  risk_level: string;
  current_pressure: number;
  current_flow: number;
  pressure_trend: string;
  flow_trend: string;
  anomalies_last_24h: number;
  incidents_last_30_days: number;
  water_loss_estimate: number;
}

export interface TelemetryTrend {
  timestamp: string;
  pressure_mca: number;
  flow_lps: number;
}

export interface AnomalyAnalysis {
  total_readings: number;
  anomalies_detected: number;
  anomaly_rate: number;
  anomalies: Array<{
    score: number;
    anomaly: Anomaly;
    features: Record<string, number>;
  }>;
}
