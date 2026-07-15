import { useParams, useNavigate } from 'react-router-dom';
import { useDma, useDmaSensors, useDmaMetrics, useTelemetryHistory, useRecentAnomalies, useIncidents } from '../../services/hooks';
import { SeverityBadge } from '../../components/StatusBadge';
import StatusBadge from '../../components/StatusBadge';
import { format } from '../../utils/format';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowLeft, Gauge, Activity, Loader2, Users } from 'lucide-react';

export default function DmaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: dma, isLoading: dmaLoading } = useDma(id ?? '');
  const { data: sensorsData } = useDmaSensors(id ?? '');
  const { data: metrics, isLoading: metLoading } = useDmaMetrics(id ?? '');
  const { data: history } = useTelemetryHistory(id ?? '');
  const { data: anomalies } = useRecentAnomalies();
  const { data: incidents } = useIncidents(id);

  const isLoading = dmaLoading || metLoading;
  const dmaAnomalies = anomalies?.anomalies ? anomalies.anomalies.filter((a: any) => (a.anomaly?.dma_id || a.dma_id) === id) : [];
  const dmaHistory = history?.readings || [];
  const sensors = sensorsData?.sensors || [];
  const incidentList = Array.isArray(incidents) ? incidents : [];

  const chartData = dmaHistory.length > 0
    ? dmaHistory.map((r) => ({ time: new Date(r.timestamp).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }), presion: r.pressure_mca, caudal: r.flow_lps }))
    : [];

  if (!id) return null;
  if (isLoading) return <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/dmas')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" /> Volver al mapa
      </button>

      {dma && (
        <div className="kpi-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-xl font-bold text-gray-900">{dma.name || dma.dma?.name}</h2>
                <StatusBadge status={dma.status || dma.dma?.status} />
              </div>
              <p className="text-sm text-gray-500">{dma.code || dma.dma?.code} — {dma.district || dma.dma?.district}</p>
            </div>
            {dma.population && (
              <div className="text-right text-sm text-gray-400 flex items-center gap-1"><Users className="w-4 h-4" />{dma.population.toLocaleString()}</div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="kpi-card"><p className="text-xs text-gray-500">Presión Actual</p><p className="text-xl font-bold text-gray-900">{metrics?.current_pressure ?? '--'} <span className="text-sm font-normal text-gray-400">MCA</span></p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Caudal Actual</p><p className="text-xl font-bold text-gray-900">{metrics?.current_flow ?? '--'} <span className="text-sm font-normal text-gray-400">LPS</span></p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Nivel de Riesgo</p><p className="text-xl font-bold"><StatusBadge status={metrics?.risk_level || 'UNKNOWN'} /></p><p className="text-xs text-gray-400 mt-1">Anomalías (24h): {metrics?.anomalies_last_24h ?? 0}</p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Pérdida Estimada</p><p className="text-xl font-bold text-gray-900">{metrics?.water_loss_estimate?.toFixed(1) ?? '--'} <span className="text-sm font-normal text-gray-400">m³/día</span></p></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Historial de Presión</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" fontSize={11} tickLine={false} interval={12} />
                <YAxis fontSize={11} tickLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="presion" stroke="#0d6ebd" strokeWidth={2} dot={false} name="Presión (MCA)" />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 py-8 text-center">Sin datos históricos</p>}
        </div>
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Historial de Caudal</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" fontSize={11} tickLine={false} interval={12} />
                <YAxis fontSize={11} tickLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="caudal" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Caudal (LPS)" />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 py-8 text-center">Sin datos históricos</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Sensores ({sensors.length})</h3>
          {sensors.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">Sin sensores registrados</p>
          ) : (
            <div className="space-y-2">
              {sensors.map((s: any) => (
                <div key={s.id || s.code} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-3">
                    {s.type === 'PRESSURE' ? <Gauge className="w-4 h-4 text-primary-500" /> : <Activity className="w-4 h-4 text-hydraulic-500" />}
                    <div>
                      <p className="text-sm font-medium text-gray-800">{s.name || s.code}</p>
                      <p className="text-xs text-gray-400">{s.code} · {s.unit}</p>
                    </div>
                  </div>
                  <StatusBadge status={s.status} />
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Anomalías Recientes</h3>
          {dmaAnomalies.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">Sin anomalías recientes</p>
          ) : (
            <div className="space-y-2">
              {dmaAnomalies.slice(0, 5).map((a: any) => {
                const an = a.anomaly || a;
                return (
                  <div key={an.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div>
                      <p className="text-sm text-gray-800">Score: {(a.score || an.anomaly_score)?.toFixed(3)}</p>
                      <p className="text-xs text-gray-400">{format.datetime(an.detected_at)}</p>
                    </div>
                    <SeverityBadge severity={an.severity} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="kpi-card">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Incidentes del Sector ({incidentList.length})</h3>
        {incidentList.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">Sin incidentes registrados</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Código</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Título</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Prioridad</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Estado</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Asignado</th>
                  <th className="text-left py-2 px-3 text-gray-500 font-medium">Creado</th>
                </tr>
              </thead>
              <tbody>
                {incidentList.map((inc) => (
                  <tr key={inc.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 px-3 font-mono text-xs">{inc.code}</td>
                    <td className="py-2 px-3 text-gray-700">{inc.title}</td>
                    <td className="py-2 px-3"><StatusBadge status={inc.priority} className="bg-orange-100 text-orange-800" /></td>
                    <td className="py-2 px-3"><StatusBadge status={inc.status} /></td>
                    <td className="py-2 px-3 text-gray-600">{inc.assigned_to || '--'}</td>
                    <td className="py-2 px-3 text-xs text-gray-500">{format.datetime(inc.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
