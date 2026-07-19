import { useEffect, useState, useRef, useCallback } from 'react';
import { useLatestTelemetry, useMocheTrends, useRecentAnomalies } from '../../services/hooks';
import StatusBadge from '../../components/StatusBadge';
import { SeverityBadge } from '../../components/StatusBadge';
import { useAuth } from '../../services/auth';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, Legend,
} from 'recharts';
import { format } from '../../utils/format';
import { Gauge, Activity, RefreshCw, Wifi, WifiOff } from 'lucide-react';

// Colores para diferenciar los sensores
const SENSOR_COLORS = [
  '#0d6ebd', '#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'
];

export default function MonitoringPage() {
  const { token } = useAuth();
  const { data: readings } = useLatestTelemetry();
  const { data: trends } = useMocheTrends();
  const { data: anomalies } = useRecentAnomalies();
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [realtimeReading, setRealtimeReading] = useState<any>(null);
  const [selectedSensors, setSelectedSensors] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    const clientId = 'monitor-' + Date.now();
    const url = `ws://localhost:8000/ws/${clientId}`;
    setWsStatus('connecting');
    try {
      const ws = new WebSocket(url);
      ws.onopen = () => { setWsStatus('connected'); };
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'TELEMETRY_UPDATE' && msg.data) {
            setRealtimeReading(msg.data);
          }
        } catch { }
      };
      ws.onclose = () => {
        setWsStatus('disconnected');
        wsRef.current = null;
        reconnectTimeoutRef.current = setTimeout(connectWs, 5000);
      };
      ws.onerror = () => {
        ws.close();
      };
      wsRef.current = ws;
    } catch {
      setWsStatus('disconnected');
      reconnectTimeoutRef.current = setTimeout(connectWs, 5000);
    }
  }, []);

  useEffect(() => {
    if (token) connectWs();
    return () => {
      wsRef.current?.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [token, connectWs]);

  const sensors = trends?.sensors || [];
  const latestReadings = Array.isArray(readings) ? readings : [];

  // Initialize selected sensors when sensors are loaded
  useEffect(() => {
    if (sensors.length > 0 && selectedSensors.length === 0) {
      setSelectedSensors(sensors.map((s: any) => s.sensor_id));
    }
  }, [sensors, selectedSensors.length]);

  const toggleSensor = (sensorId: string) => {
    if (selectedSensors.includes(sensorId)) {
      // Don't allow deselecting all sensors
      if (selectedSensors.length > 1) {
        setSelectedSensors(selectedSensors.filter(id => id !== sensorId));
      }
    } else {
      setSelectedSensors([...selectedSensors, sensorId]);
    }
  };

  const filteredSensors = sensors.filter((sensor: any) => selectedSensors.includes(sensor.sensor_id));

  // Preparar datos para gráficos de presión
  const prepareChartData = (dataType: 'pressure' | 'flow') => {
    if (filteredSensors.length === 0) return [];
    
    // Obtener timestamps únicos ordenados
    const allTimestamps = new Set<string>();
    filteredSensors.forEach((sensor: any) => {
      (sensor[dataType] || []).forEach((p: any) => allTimestamps.add(p.timestamp));
    });
    const sortedTimestamps = Array.from(allTimestamps).sort();
    
    // Crear objeto por timestamp con valores de cada sensor
    return sortedTimestamps.map(ts => {
      const time = new Date(ts).toLocaleTimeString('es-PE', { 
        hour: '2-digit', minute: '2-digit', hourCycle: 'h23' 
      });
      const point: any = { time };
      
      filteredSensors.forEach((sensor: any, index: number) => {
        const reading = (sensor[dataType] || []).find((r: any) => r.timestamp === ts);
        if (reading) {
          point[sensor.sensor_id] = reading.value;
        }
      });
      
      return point;
    });
  };

  const pressureChartData = prepareChartData('pressure');
  const flowChartData = prepareChartData('flow');

  const anomalyList = anomalies?.anomalies || [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {latestReadings.map((reading: any, index: number) => (
          <div key={reading.sensor_id} className="kpi-card">
            <div className="flex items-center gap-3 mb-3">
              <div 
                className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ 
                  background: `linear-gradient(135deg, ${SENSOR_COLORS[index % SENSOR_COLORS.length]}, ${SENSOR_COLORS[(index + 1) % SENSOR_COLORS.length]})` 
                }}
              >
                <Gauge className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 truncate">{reading.sensor_id}</p>
                <p className="text-lg font-bold text-gray-900">{reading.pressure_mca} <span className="text-sm font-normal text-gray-400">MCA</span></p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Caudal: {reading.flow_lps} LPS</span>
              <StatusBadge status={reading.quality_flag ?? '--'} className="ml-auto" />
            </div>
          </div>
        ))}
        
        <div className="kpi-card">
          <p className="text-xs text-gray-500 mb-1">Conexión WebSocket</p>
          <div className="flex items-center gap-2 mt-2">
            {wsStatus === 'connected' ? <Wifi className="w-5 h-5 text-green-500" /> : wsStatus === 'connecting' ? <RefreshCw className="w-5 h-5 text-yellow-500 animate-spin" /> : <WifiOff className="w-5 h-5 text-red-500" />}
            <span className={`text-sm font-medium ${wsStatus === 'connected' ? 'text-green-600' : wsStatus === 'connecting' ? 'text-yellow-600' : 'text-red-600'}`}>
              {wsStatus === 'connected' ? 'Conectado' : wsStatus === 'connecting' ? 'Conectando...' : 'Desconectado'}
            </span>
          </div>
          {wsStatus === 'disconnected' && (
            <button onClick={connectWs} className="mt-2 text-xs text-hydraulic-600 hover:underline">Reconectar</button>
          )}
        </div>
      </div>

      <div className="kpi-card">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Seleccionar Sensores</h3>
        <div className="flex flex-wrap gap-4">
          {sensors.map((sensor: any, index: number) => (
            <label key={sensor.sensor_id} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedSensors.includes(sensor.sensor_id)}
                onChange={() => toggleSensor(sensor.sensor_id)}
                disabled={selectedSensors.length === 1 && selectedSensors.includes(sensor.sensor_id)}
                className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500 disabled:opacity-50"
              />
              <span className="text-sm text-gray-700 flex items-center gap-1">
                <span 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: SENSOR_COLORS[index % SENSOR_COLORS.length] }}
                />
                {sensor.sensor_name}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Presión - Tendencia por Sensor</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={pressureChartData}>
              <defs>
                {filteredSensors.map((sensor: any, index: number) => {
                  const originalIndex = sensors.findIndex((s: any) => s.sensor_id === sensor.sensor_id);
                  return (
                    <linearGradient key={sensor.sensor_id} id={`pg-${sensor.sensor_id}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={SENSOR_COLORS[originalIndex % SENSOR_COLORS.length]} stopOpacity={0.15} />
                      <stop offset="95%" stopColor={SENSOR_COLORS[originalIndex % SENSOR_COLORS.length]} stopOpacity={0} />
                    </linearGradient>
                  );
                })}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" fontSize={11} tickLine={false} minTickGap={60} />
              <YAxis fontSize={11} tickLine={false} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {filteredSensors.map((sensor: any) => {
                const originalIndex = sensors.findIndex((s: any) => s.sensor_id === sensor.sensor_id);
                return (
                  <Area
                    key={sensor.sensor_id}
                    type="monotone"
                    dataKey={sensor.sensor_id}
                    name={sensor.sensor_name}
                    stroke={SENSOR_COLORS[originalIndex % SENSOR_COLORS.length]}
                    strokeWidth={2}
                    fill={`url(#pg-${sensor.sensor_id})`}
                  />
                );
              })}
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Caudal - Tendencia por Sensor</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={flowChartData}>
              <defs>
                {filteredSensors.map((sensor: any) => {
                  const originalIndex = sensors.findIndex((s: any) => s.sensor_id === sensor.sensor_id);
                  return (
                    <linearGradient key={sensor.sensor_id} id={`fg-${sensor.sensor_id}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={SENSOR_COLORS[originalIndex % SENSOR_COLORS.length]} stopOpacity={0.15} />
                      <stop offset="95%" stopColor={SENSOR_COLORS[originalIndex % SENSOR_COLORS.length]} stopOpacity={0} />
                    </linearGradient>
                  );
                })}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" fontSize={11} tickLine={false} minTickGap={60} />
              <YAxis fontSize={11} tickLine={false} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {filteredSensors.map((sensor: any) => {
                const originalIndex = sensors.findIndex((s: any) => s.sensor_id === sensor.sensor_id);
                return (
                  <Area
                    key={sensor.sensor_id}
                    type="monotone"
                    dataKey={sensor.sensor_id}
                    name={sensor.sensor_name}
                    stroke={SENSOR_COLORS[originalIndex % SENSOR_COLORS.length]}
                    strokeWidth={2}
                    fill={`url(#fg-${sensor.sensor_id})`}
                  />
                );
              })}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="kpi-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-700">Eventos Detectados</h3>
          {anomalyList.length > 0 && <span className="text-xs text-gray-400">{anomalyList.length} eventos</span>}
        </div>
        {anomalyList.length === 0 ? (
          <p className="text-sm text-gray-400 py-6 text-center">No se detectaron eventos anómalos en las últimas 24 horas</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Fecha</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Sensor</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Score</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Severidad</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Estado</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Pérdida Est.</th>
                </tr>
              </thead>
              <tbody>
                {anomalyList.map((a: any) => {
                  const an = a.anomaly || a;
                  return (
                    <tr key={an.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 px-3 text-gray-700">{format.datetime(an.detected_at)}</td>
                      <td className="py-2 px-3 text-gray-700">{an.sensor_id || an.dma_id}</td>
                      <td className="py-2 px-3"><span className="font-mono text-sm">{a.score?.toFixed(3) || an.anomaly_score?.toFixed(3)}</span></td>
                      <td className="py-2 px-3"><SeverityBadge severity={an.severity} /></td>
                      <td className="py-2 px-3"><StatusBadge status={an.status} /></td>
                      <td className="py-2 px-3 text-gray-700">{an.estimated_loss_volume?.toFixed(1) ?? '--'} m³</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
