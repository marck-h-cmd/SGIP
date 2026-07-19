import { useExecutiveKpis, useLatestTelemetry, useAlerts, useRecentAnomalies, useIncidents, useMocheTrends } from '../../services/hooks';
import KpiCard from '../../components/KpiCard';
import StatusBadge, { SeverityBadge } from '../../components/StatusBadge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Droplets, AlertTriangle, Ticket, Clock, Activity, Gauge, Map as MapIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { format } from '../../utils/format';
import { useState, useEffect } from 'react';

// Colores para diferenciar los sensores
const SENSOR_COLORS = [
  '#0d6ebd', '#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'
];

export default function DashboardPage() {
  const { data: kpis } = useExecutiveKpis();
  const { data: readings } = useLatestTelemetry();
  const { data: alerts } = useAlerts();
  const { data: anomalies } = useRecentAnomalies();
  const { data: incidents } = useIncidents();
  const { data: trends } = useMocheTrends();
  const navigate = useNavigate();
  const [selectedSensors, setSelectedSensors] = useState<string[]>([]);

  const criticalAlerts = Array.isArray(alerts) ? alerts.filter((a: any) => a.severity === 'CRITICAL' && !a.acknowledged) : [];
  const criticalCount = criticalAlerts.length;
  const activeIncidents = kpis?.active_incidents ?? (Array.isArray(incidents) ? incidents.filter((i: any) => i.status && !['RESOLVED', 'CLOSED'].includes(i.status)).length : 0);
  
  let latest: any = null;
  if (Array.isArray(readings) && readings.length > 0) {
    latest = readings[0];
  } else if (readings && typeof readings === 'object' && 'pressure_mca' in readings) {
    latest = readings;
  }

  const sensors = trends?.sensors || [];

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

  const anomalyList = anomalies?.anomalies || [];
  const incidentList = Array.isArray(incidents) ? incidents : [];

  let chartData: any[] = [];
  if (trends && typeof trends === 'object' && !Array.isArray(trends)) {
    const t = trends as any;
    let useSensors = false;
    let workingSensors: any[] = [];
    
    if (Array.isArray(t.sensors) && t.sensors.length > 0) {
      useSensors = true;
      workingSensors = filteredSensors;
    }
    
    if (useSensors && workingSensors.length > 0) {
      // Obtener timestamps únicos ordenados
      const allTimestamps = new Set<string>();
      workingSensors.forEach((sensor: any) => {
        (sensor.flow || []).forEach((p: any) => allTimestamps.add(p.timestamp));
      });
      const sortedTimestamps = Array.from(allTimestamps).sort();
      
      // Crear objeto por timestamp con valores de cada sensor
      chartData = sortedTimestamps.map(ts => {
        const time = new Date(ts).toLocaleTimeString('es-PE', { 
          hour: '2-digit', minute: '2-digit', hourCycle: 'h23' 
        });
        const point: any = { time };
        
        workingSensors.forEach((sensor: any) => {
          const pressureReading = (sensor.pressure || []).find((r: any) => r.timestamp === ts);
          const flowReading = (sensor.flow || []).find((r: any) => r.timestamp === ts);
          if (pressureReading) {
            point[`${sensor.sensor_id}_presion`] = pressureReading.value;
          }
          if (flowReading) {
            point[`${sensor.sensor_id}_caudal`] = flowReading.value;
          }
        });
        
        return point;
      });
    } else {
      // Fall back to old format
      let pressureArray: any[] = [];
      let flowArray: any[] = [];
      
      if (Array.isArray(t.pressure) && Array.isArray(t.flow)) {
        pressureArray = t.pressure;
        flowArray = t.flow;
      } else if (Array.isArray(t.sensors) && t.sensors.length > 0) {
        const firstSensor = t.sensors[0];
        if (Array.isArray(firstSensor.pressure) && Array.isArray(firstSensor.flow)) {
          pressureArray = firstSensor.pressure;
          flowArray = firstSensor.flow;
        }
      }
      
      if (flowArray.length > 0) {
        const pressureMap = new Map(pressureArray.map((p: any) => [p.timestamp, p.value]));
        chartData = flowArray.map((f: any) => ({
          time: new Date(f.timestamp).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }),
          presion: pressureMap.get(f.timestamp) ?? 0,
          caudal: f.value ?? 0,
        }));
      }
    }
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 kpi-card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Tendencia de Presión y Caudal</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" fontSize={12} tickLine={false} minTickGap={60} />
              <YAxis yAxisId="left" fontSize={12} tickLine={false} />
              <YAxis yAxisId="right" orientation="right" fontSize={12} tickLine={false} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              {filteredSensors.length > 0 ? filteredSensors.map((sensor: any) => {
                const originalIndex = sensors.findIndex((s: any) => s.sensor_id === sensor.sensor_id);
                const color = SENSOR_COLORS[originalIndex % SENSOR_COLORS.length];
                return (
                  <>
                    <Line 
                      yAxisId="left" 
                      type="monotone" 
                      dataKey={`${sensor.sensor_id}_presion`} 
                      stroke={color} 
                      strokeWidth={2} 
                      dot={false} 
                      name={`Presión - ${sensor.sensor_name}`} 
                    />
                    <Line 
                      yAxisId="right" 
                      type="monotone" 
                      dataKey={`${sensor.sensor_id}_caudal`} 
                      stroke={color} 
                      strokeWidth={2} 
                      dot={false} 
                      name={`Caudal - ${sensor.sensor_name}`} 
                      strokeDasharray="5 5"
                    />
                  </>
                );
              }) : (
                <>
                  <Line yAxisId="left" type="monotone" dataKey="presion" stroke="#0d6ebd" strokeWidth={2} dot={false} name="Presión (MCA)" />
                  <Line yAxisId="right" type="monotone" dataKey="caudal" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Caudal (LPS)" />
                </>
              )}
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
                  <StatusBadge status={latest.quality_flag || 'NORMAL'} />
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
              {anomalyList.slice(0, 5).map((a: any) => {
                const an = a.anomaly || a;
                return (
                  <div key={an?.id || Math.random()} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{an?.description || a?.description || `Anomalía #${an?.id || a?.id}`}</p>
                      <p className="text-xs text-gray-400">{format.datetime(an?.detected_at || a?.detected_at)}</p>
                    </div>
                    <SeverityBadge severity={an?.severity || a?.severity} />
                  </div>
                );
              })}
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
              {incidentList.slice(0, 5).map((inc: any) => (
                <div key={inc?.id || Math.random()} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{inc?.code}</p>
                    <p className="text-xs text-gray-400">{inc?.title}</p>
                  </div>
                  <StatusBadge status={inc?.status} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
