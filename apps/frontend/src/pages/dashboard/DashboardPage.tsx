import { useExecutiveKpis, useLatestTelemetry, useAlerts, useRecentAnomalies, useIncidents, useMocheTrends } from '../../services/hooks';
import KpiCard from '../../components/KpiCard';
import StatusBadge, { SeverityBadge } from '../../components/StatusBadge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Droplets, AlertTriangle, Ticket, Clock, Activity, Gauge, Map as MapIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { format } from '../../utils/format';

export default function DashboardPage() {
  const { data: kpis } = useExecutiveKpis();
  const { data: readings } = useLatestTelemetry();
  const { data: alerts } = useAlerts();
  const { data: anomalies } = useRecentAnomalies();
  const { data: incidents } = useIncidents();
  const { data: trends } = useMocheTrends();
  const navigate = useNavigate();

  const criticalAlerts = Array.isArray(alerts) ? alerts.filter((a: any) => a.severity === 'CRITICAL' && !a.acknowledged) : [];
  const criticalCount = criticalAlerts.length;
  const activeIncidents = kpis?.active_incidents ?? (Array.isArray(incidents) ? incidents.filter((i) => !['RESOLVED', 'CLOSED'].includes(i.status)).length : 0);
  const latest = Array.isArray(readings) ? readings[0] : null;
  const anomalyList = anomalies?.anomalies || [];
  const incidentList = Array.isArray(incidents) ? incidents : [];

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

  return (
    <div className="space-y-6">
      {criticalCount > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-red-600 shrink-0" />
          <div className="flex-1">
            <p className="font-semibold text-red-800">{criticalCount} alerta(s) crítica(s) sin atender</p>
          </div>
          <button onClick={() => navigate('/incidents')} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 shrink-0">Revisar</button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="DMAs Monitoreados" value={kpis?.total_dmas ?? 5} icon={<MapIcon className="w-5 h-5" />} color="blue" />
        <KpiCard title="Incidencias Activas" value={activeIncidents} icon={<Ticket className="w-5 h-5" />} color={activeIncidents > 0 ? 'red' : 'green'} trend={activeIncidents > 0 ? 'up' : 'down'} />
        <KpiCard title="Tiempo Prom. Detección" value={kpis?.avg_detection_time_hours ? `${kpis.avg_detection_time_hours.toFixed(1)}h` : '--'} icon={<Clock className="w-5 h-5" />} color="purple" />
        <KpiCard title="Pérdida Estimada" value={kpis?.water_loss_estimate_m3 ? `${kpis.water_loss_estimate_m3.toFixed(0)} m³/día` : '--'} icon={<Droplets className="w-5 h-5" />} color="blue" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Tendencia de Presión y Caudal</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" fontSize={12} tickLine={false} interval={12} />
              <YAxis yAxisId="left" fontSize={12} tickLine={false} />
              <YAxis yAxisId="right" orientation="right" fontSize={12} tickLine={false} />
              <Tooltip />
              <Line yAxisId="left" type="monotone" dataKey="presion" stroke="#0d6ebd" strokeWidth={2} dot={false} name="Presión (MCA)" />
              <Line yAxisId="right" type="monotone" dataKey="caudal" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Caudal (LPS)" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-4">
          <div className="kpi-card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Lectura Actual</h3>
            {latest ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg">
                  <div className="flex items-center gap-2"><Gauge className="w-5 h-5 text-primary-500" /><span className="text-sm text-gray-600">Presión</span></div>
                  <span className="text-lg font-bold text-primary-700">{latest.pressure_mca} MCA</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gradient-to-r from-hydraulic-50 to-cyan-50 rounded-lg">
                  <div className="flex items-center gap-2"><Activity className="w-5 h-5 text-hydraulic-500" /><span className="text-sm text-gray-600">Caudal</span></div>
                  <span className="text-lg font-bold text-hydraulic-700">{latest.flow_lps} LPS</span>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{latest.dma_id}</span>
                  <StatusBadge status={latest.quality_flag} />
                </div>
              </div>
            ) : <p className="text-sm text-gray-400 py-4 text-center">Sin datos</p>}
          </div>
          <div className="kpi-card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">SLA Cumplimiento</h3>
            <div className="flex items-center gap-3">
              <div className="relative w-16 h-16">
                <svg className="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="#e5e7eb" strokeWidth="3" />
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="#0d6ebd" strokeWidth="3" strokeDasharray={`${(kpis?.sla_compliance ?? 0) * 0.97} 100`} />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-gray-700">{kpis?.sla_compliance ? `${kpis.sla_compliance}%` : '--'}</span>
              </div>
              <div className="text-xs text-gray-500"><p>Índice de cumplimiento</p><p className="text-green-600 font-medium">Objetivo: &gt;95%</p></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="kpi-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Últimas Anomalías</h3>
            <button onClick={() => navigate('/analytics')} className="text-xs text-hydraulic-600 hover:underline">Ver todas</button>
          </div>
          {anomalyList.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">No hay anomalías recientes</p>
          ) : (
            <div className="space-y-2">
              {anomalyList.slice(0, 5).map((a: any) => (
                <div key={a.id || a.anomaly?.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{a.description || a.anomaly?.description || `Anomalía #${a.anomaly?.id || a.id}`}</p>
                    <p className="text-xs text-gray-400">{format.datetime(a.detected_at || a.anomaly?.detected_at)}</p>
                  </div>
                  <SeverityBadge severity={a.severity || a.anomaly?.severity} />
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="kpi-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Incidentes Recientes</h3>
            <button onClick={() => navigate('/incidents')} className="text-xs text-hydraulic-600 hover:underline">Ver todos</button>
          </div>
          {incidentList.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">No hay incidentes registrados</p>
          ) : (
            <div className="space-y-2">
              {incidentList.slice(0, 5).map((inc) => (
                <div key={inc.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{inc.code}</p>
                    <p className="text-xs text-gray-400">{inc.title}</p>
                  </div>
                  <StatusBadge status={inc.status} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
