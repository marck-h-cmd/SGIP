import { useEffect, useState, useRef, useCallback } from 'react';
import { useLatestTelemetry, useMocheTrends, useRecentAnomalies } from '../../services/hooks';
import StatusBadge from '../../components/StatusBadge';
import { SeverityBadge } from '../../components/StatusBadge';
import { useAuth } from '../../services/auth';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from 'recharts';
import { format } from '../../utils/format';
import { Gauge, Activity, RefreshCw, Wifi, WifiOff } from 'lucide-react';

export default function MonitoringPage() {
  const { token } = useAuth();
  const { data: readings } = useLatestTelemetry();
  const { data: trends } = useMocheTrends();
  const { data: anomalies } = useRecentAnomalies();
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [realtimeReading, setRealtimeReading] = useState<any>(null);
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
        } catch {}
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

  const latest = realtimeReading || (Array.isArray(readings) ? readings[0] : null);
  let chartData: { time: string; presion: number; caudal: number }[] = [];
  if (trends && typeof trends === 'object' && !Array.isArray(trends)) {
    const t = trends as any;
    if (Array.isArray(t.pressure) && Array.isArray(t.flow)) {
      const pressureMap = new Map(t.pressure.map((p: any) => [p.timestamp, p.value]));
      chartData = t.flow.map((f: any) => ({
        time: new Date(f.timestamp).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }),
        presion: pressureMap.get(f.timestamp) ?? 0,
        caudal: f.value ?? 0,
      }));
    }
  } else if (Array.isArray(trends)) {
    chartData = trends.map((t: any) => ({
      time: new Date(t.timestamp).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }),
      presion: t.pressure_mca, caudal: t.flow_lps,
    }));
  }
  const anomalyList = anomalies?.anomalies || [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="kpi-card">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center"><Gauge className="w-5 h-5 text-white" /></div>
            <div>
              <p className="text-xs text-gray-500">Presión Actual</p>
              <p className="text-2xl font-bold text-gray-900">{latest?.pressure_mca ?? '--'} <span className="text-sm font-normal text-gray-400">MCA</span></p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <StatusBadge status={latest?.quality_flag ?? '--'} className="ml-auto" />
          </div>
        </div>
        <div className="kpi-card">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-hydraulic-500 to-hydraulic-700 flex items-center justify-center"><Activity className="w-5 h-5 text-white" /></div>
            <div>
              <p className="text-xs text-gray-500">Caudal Actual</p>
              <p className="text-2xl font-bold text-gray-900">{latest?.flow_lps ?? '--'} <span className="text-sm font-normal text-gray-400">LPS</span></p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>{latest?.dma_id || 'DMA-MO-01'}</span>
          </div>
        </div>
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
        <div className="kpi-card">
          <p className="text-xs text-gray-500 mb-1">Fuente de Datos</p>
          <p className="text-lg font-bold text-gray-900">{latest?.source || 'Mock'}</p>
          <p className="text-xs text-gray-400 mt-1">Sensor: {latest?.sensor_id || '--'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Presión — Tendencia</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData.length > 0 ? chartData : [{ time: '--', presion: 0, caudal: 0 }]}>
              <defs><linearGradient id="pg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#0d6ebd" stopOpacity={0.2} /><stop offset="95%" stopColor="#0d6ebd" stopOpacity={0} /></linearGradient></defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" fontSize={11} tickLine={false} interval={12} />
              <YAxis fontSize={11} tickLine={false} />
              <Tooltip />
              <Area type="monotone" dataKey="presion" stroke="#0d6ebd" strokeWidth={2} fill="url(#pg)" name="Presión (MCA)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Caudal — Tendencia</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData.length > 0 ? chartData : [{ time: '--', presion: 0, caudal: 0 }]}>
              <defs><linearGradient id="fg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.2} /><stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} /></linearGradient></defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" fontSize={11} tickLine={false} interval={12} />
              <YAxis fontSize={11} tickLine={false} />
              <Tooltip />
              <Area type="monotone" dataKey="caudal" stroke="#0ea5e9" strokeWidth={2} fill="url(#fg)" name="Caudal (LPS)" />
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
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">DMA</th>
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
                      <td className="py-2 px-3 text-gray-700">{an.dma_id}</td>
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
