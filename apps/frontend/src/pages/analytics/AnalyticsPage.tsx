import { useState } from 'react';
import { useAnomalyStats, useRecentAnomalies, useTelemetryHistory } from '../../services/hooks';
import StatusBadge, { SeverityBadge } from '../../components/StatusBadge';
import { format } from '../../utils/format';
import { api } from '../../services/api';
import { useQueryClient } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter, ZAxis, Legend } from 'recharts';
import { Brain, TrendingUp, AlertTriangle, Target, Activity, Loader2, Play } from 'lucide-react';

const severityColors = ['#ef4444', '#f97316', '#eab308', '#22c55e'];
const mlInfo = {
  model: 'Isolation Forest',
  algorithm: 'Ensemble de árboles de aislamiento',
  threshold: 0.75,
  features: ['Presión (MCA)', 'Caudal (LPS)', 'Hora del día', 'Día de la semana', 'Media móvil 1h', 'Desviación estándar'],
  training: 'Automático — ventana de 30 días',
};

export default function AnalyticsPage() {
  const queryClient = useQueryClient();
  const [isSimulating, setIsSimulating] = useState(false);
  const { data: stats, isLoading: stLoading } = useAnomalyStats();
  const { data: anomaliesData, isLoading: anLoading } = useRecentAnomalies();
  const { data: telemetryHistory } = useTelemetryHistory('DMA-MO-01', 24);
  const isLoading = stLoading || anLoading;

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      await api.anomalies.simulate();
      // Invalidate with exact query keys defined in hooks.ts
      await queryClient.invalidateQueries({ queryKey: ['anomalies-recent'] });
      await queryClient.invalidateQueries({ queryKey: ['anomaly-stats'] });
      await queryClient.invalidateQueries({ queryKey: ['telemetry-history'] });
    } catch (e) {
      console.error(e);
    } finally {
      setIsSimulating(false);
    }
  };

  const anomalies = anomaliesData?.anomalies || [];
  const severityCount: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
  anomalies.forEach((a: any) => {
    const sev = a.anomaly?.severity || a.severity;
    if (sev && sev in severityCount) severityCount[sev]++;
  });
  const pieData = Object.entries(severityCount).filter(([, v]) => v > 0).map(([name, value]) => ({ name, value }));
  
  const anomalyHistory = stats?.history_7d || [];
  
  const normalData: any[] = [];
  const anomalyData: any[] = [];
  
  telemetryHistory?.readings?.forEach((r: any) => {
    const isAnomaly = r.pressure_mca < 40 || r.flow_lps > 35;
    // Jitter visual para evitar superposiciones exactas
    const jitterP = (Math.random() - 0.5) * 1.5;
    const jitterF = (Math.random() - 0.5) * 1.5;
    const pt = {
      presion: Number((r.pressure_mca + jitterP).toFixed(1)),
      caudal: Number((r.flow_lps + jitterF).toFixed(1)),
    };
    if (isAnomaly) anomalyData.push(pt);
    else normalData.push(pt);
  });
  
  const latestAnomaly = anomalies[0]?.anomaly || anomalies[0];

  // --- Explicabilidad del Modelo ---
  // Calcula el impacto relativo de cada variable respecto al baseline normal
  // Baselines: presión normal ~55.2 MCA, caudal normal ~25.4 LPS
  const PRESSURE_BASELINE = 55.2;
  const FLOW_BASELINE = 25.4;
  const pressureVar = latestAnomaly?.pressure_variation ?? 0;
  const flowVar = latestAnomaly?.flow_variation ?? 0;
  // Impacto = |desviación| / baseline → normalizado a porcentaje
  const importanceP = Math.abs(pressureVar) / PRESSURE_BASELINE;
  const importanceF = Math.abs(flowVar) / FLOW_BASELINE;
  const totalImp = importanceP + importanceF + 0.0001;
  const pctP = Math.min(100, Math.round((importanceP / totalImp) * 100));
  const pctF = Math.min(100, Math.round((importanceF / totalImp) * 100));
  // Valores reales registrados = baseline + variación
  const realPressure = latestAnomaly ? PRESSURE_BASELINE + pressureVar : null;
  const realFlow = latestAnomaly ? FLOW_BASELINE + flowVar : null;

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="kpi-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center"><Brain className="w-5 h-5 text-white" /></div>
            <div><p className="text-xs text-gray-500">Modelo</p><p className="text-lg font-bold text-gray-900">Isolation Forest</p></div>
          </div>
        </div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Umbral de Detección</p><p className="text-2xl font-bold text-gray-900">{stats?.threshold || mlInfo.threshold}</p><p className="text-xs text-gray-400">Score mínimo para anomalía</p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Total Anomalías</p><p className="text-2xl font-bold text-gray-900">{stats?.total_anomalies_24h ?? anomalies.length}</p><p className="text-xs text-gray-400">Últimas 24h</p></div>
        <div className="kpi-card"><p className="text-xs text-gray-500">Tasa de Detección</p><p className="text-2xl font-bold text-gray-900">{stats?.avg_score ? `${(Number(stats.avg_score) * 100).toFixed(1)}%` : '--'}</p><p className="text-xs text-gray-400">Score promedio</p></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Distribución por Severidad</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                  {pieData.map((_, i) => <Cell key={i} fill={severityColors[i]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 py-12 text-center">Sin datos de severidad</p>}
        </div>
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Historial de Detecciones (7 días)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={anomalyHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="dia" fontSize={11} tickLine={false} />
              <YAxis fontSize={11} tickLine={false} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="anomalias" fill="#0d6ebd" radius={[4, 4, 0, 0]} name="Anomalías" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="kpi-card">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Información del Modelo ML</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center gap-2"><Target className="w-4 h-4 text-primary-500" /><span className="text-sm font-medium text-gray-700">Algoritmo</span></div>
            <p className="text-sm text-gray-600 ml-6">{mlInfo.algorithm}</p>
            <div className="flex items-center gap-2 mt-4"><Activity className="w-4 h-4 text-primary-500" /><span className="text-sm font-medium text-gray-700">Variables de Entrada</span></div>
            <ul className="ml-6 space-y-1">
              {(stats?.features || mlInfo.features).map((f: string, i: number) => (<li key={i} className="text-sm text-gray-600 flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-primary-400" />{f}</li>))}
            </ul>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2"><TrendingUp className="w-4 h-4 text-primary-500" /><span className="text-sm font-medium text-gray-700">Entrenamiento</span></div>
            <p className="text-sm text-gray-600 ml-6">{mlInfo.training}</p>
            <div className="flex items-center gap-2 mt-4"><AlertTriangle className="w-4 h-4 text-primary-500" /><span className="text-sm font-medium text-gray-700">Método</span></div>
            <p className="text-sm text-gray-600 ml-6">Detección no supervisada de anomalías. El modelo aprende el comportamiento normal de presión y caudal, e identifica desviaciones significativas. Arquitectura preparada para migrar a LSTM en fases posteriores.</p>
          </div>
        </div>
      </div>

      <div className="kpi-card">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Matriz de Comportamiento (Presión vs Caudal)</h3>
        {(normalData.length > 0 || anomalyData.length > 0) ? (
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="caudal" type="number" name="Caudal" unit=" LPS" fontSize={12} tickLine={false} domain={['auto', 'auto']} />
              <YAxis dataKey="presion" type="number" name="Presión" unit=" MCA" fontSize={12} tickLine={false} domain={['auto', 'auto']} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Scatter name="Comportamiento Normal" data={normalData} fill="#0ea5e9" />
              <Scatter name="Anomalía Detectada" data={anomalyData} fill="#ef4444" />
            </ScatterChart>
          </ResponsiveContainer>
        ) : <p className="text-sm text-gray-400 py-12 text-center">Sin datos recientes para matriz</p>}
      </div>

      <div className="kpi-card">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 gap-3">
          <h3 className="text-sm font-semibold text-gray-700">Últimas Anomalías Detectadas</h3>
          <button 
            onClick={handleSimulate} 
            disabled={isSimulating}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-white bg-red-500 rounded-md hover:bg-red-600 transition-colors disabled:opacity-50"
          >
            {isSimulating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
            {isSimulating ? 'Inyectando...' : 'Simular Anomalía Crítica'}
          </button>
        </div>
        {anomalies.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">No hay registros</p>
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
                {anomalies.slice(0, 20).map((a: any) => {
                  const an = a.anomaly || a;
                  return (
                    <tr key={an.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 px-3 text-xs text-gray-600">{format.datetime(an.detected_at)}</td>
                      <td className="py-2 px-3 text-gray-700">{an.dma_id}</td>
                      <td className="py-2 px-3 font-mono text-sm">{(a.score || an.anomaly_score)?.toFixed(3)}</td>
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

      {latestAnomaly && (
        <div className="kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Explicabilidad del Modelo (Última Anomalía)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
            <div>
              <p className="text-sm text-gray-600 mb-4">
                El modelo Isolation Forest determinó que el evento del <strong>{format.datetime(latestAnomaly.detected_at)}</strong> es una anomalía de severidad <strong>{latestAnomaly.severity}</strong>.
              </p>
              {(pressureVar === 0 && flowVar === 0) ? (
                <p className="text-xs text-gray-400 italic">Sin datos de variación registrados para esta anomalía.</p>
              ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Impacto de la Presión</span>
                  <span className="text-sm font-bold text-purple-500">{pctP}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-purple-500 h-2 rounded-full transition-all duration-500" style={{ width: `${pctP}%` }}></div>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-sm font-medium text-gray-700">Impacto del Caudal</span>
                  <span className="text-sm font-bold text-sky-500">{pctF}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-sky-500 h-2 rounded-full transition-all duration-500" style={{ width: `${pctF}%` }}></div>
                </div>
              </div>
              )}
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
              <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3">Valores Registrados</h4>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-500">Presión medida</span>
                <span className="text-sm font-mono text-red-600">
                  {realPressure !== null ? `${realPressure.toFixed(1)} MCA` : '--'}
                </span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-500">Caudal medido</span>
                <span className="text-sm font-mono text-red-600">
                  {realFlow !== null ? `${realFlow.toFixed(1)} LPS` : '--'}
                </span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-500">Variación Presión</span>
                <span className="text-sm font-mono text-orange-600">
                  {pressureVar !== 0 ? `${pressureVar > 0 ? '+' : ''}${pressureVar.toFixed(2)} MCA` : '--'}
                </span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-500">Variación Caudal</span>
                <span className="text-sm font-mono text-orange-600">
                  {flowVar !== 0 ? `${flowVar > 0 ? '+' : ''}${flowVar.toFixed(2)} LPS` : '--'}
                </span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-gray-200 mt-2">
                <span className="text-sm font-medium text-gray-700">Score Final</span>
                <span className="text-sm font-bold text-gray-900">{latestAnomaly.anomaly_score?.toFixed(3) ?? '--'}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
