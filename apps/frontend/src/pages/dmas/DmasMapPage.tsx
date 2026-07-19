import { useDmas, useLatestTelemetry } from '../../services/hooks';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StatusBadge from '../../components/StatusBadge';
import { Loader2, MapPin } from 'lucide-react';

const defaultDmas = [
  { code: 'DMA-MO-01', name: 'Moche 01', district: 'Moche', latitude: -8.1700, longitude: -79.0050, status: 'ACTIVE' },
  { code: 'DMA-EP-01', name: 'El Porvenir 01', district: 'El Porvenir', latitude: -8.0800, longitude: -79.0150, status: 'ACTIVE' },
  { code: 'DMA-EP-02', name: 'El Porvenir 02', district: 'El Porvenir', latitude: -8.0750, longitude: -79.0200, status: 'WARNING' },
  { code: 'DMA-VL-01', name: 'Víctor Larco 01', district: 'Víctor Larco', latitude: -8.1400, longitude: -79.0500, status: 'ACTIVE' },
  { code: 'DMA-LE-01', name: 'La Esperanza 01', district: 'La Esperanza', latitude: -8.0600, longitude: -79.0400, status: 'CRITICAL' },
];

// Datos de sensores mock para el caso inicial
const defaultSensors = [
  { code: 'SENS-MO-01-P', dma_id: 'DMA-MO-01', name: 'Sensor de Presión Moche 01 - Norte', type: 'PRESSURE', status: 'ACTIVE', latitude: -8.1700, longitude: -79.0050 },
  { code: 'SENS-MO-01-F', dma_id: 'DMA-MO-01', name: 'Sensor de Caudal Moche 01 - Norte', type: 'FLOW', status: 'ACTIVE', latitude: -8.1702, longitude: -79.0048 },
  { code: 'SENS-MO-02-P', dma_id: 'DMA-MO-01', name: 'Sensor de Presión Moche 02 - Sur', type: 'PRESSURE', status: 'ACTIVE', latitude: -8.1750, longitude: -79.0100 },
  { code: 'SENS-MO-02-F', dma_id: 'DMA-MO-01', name: 'Sensor de Caudal Moche 02 - Sur', type: 'FLOW', status: 'ACTIVE', latitude: -8.1752, longitude: -79.0098 },
];

// Colores para los sensores
const SENSOR_COLORS = [
  '#0d6ebd', '#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'
];

function getDmaMarkerIcon(status: string) {
  const color = status === 'CRITICAL' ? '#ef4444' : status === 'WARNING' ? '#eab308' : '#22c55e';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="width:32px;height:32px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center"><svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/></svg></div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

function getSensorMarkerIcon(color: string, hasAnomaly: boolean) {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="width:24px;height:24px;border-radius:50%;background:${hasAnomaly ? '#ef4444' : color};border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.2);display:flex;align-items:center;justify-content:center"><svg width="12" height="12" viewBox="0 0 24 24" fill="white"><circle cx="12" cy="12" r="4"/></svg></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

export default function DmasMapPage() {
  const { data: apiDmas, isLoading } = useDmas();
  const { data: readings } = useLatestTelemetry();
  const navigate = useNavigate();
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => { setMapReady(true); }, []);

  const dmas = apiDmas && apiDmas.length > 0
    ? apiDmas.map((d) => ({ code: d.code, name: d.name, district: d.district, latitude: d.latitude, longitude: d.longitude, status: d.status }))
    : defaultDmas;

  // Obtener datos de sensores (usando datos mock o del provider)
  const allReadings = Array.isArray(readings) ? readings : [];
  const sensorsByDma: Record<string, any[]> = {};
  
  // Agrupar lecturas por sensor
  allReadings.forEach(r => {
    if (!sensorsByDma[r.dma_id]) sensorsByDma[r.dma_id] = [];
    sensorsByDma[r.dma_id].push(r);
  });

  // Determinar el estado del DMA basado en las lecturas de sus sensores
  const getDmaStatus = (dmaCode: string) => {
    const dmaReadings = sensorsByDma[dmaCode] || [];
    const hasCritical = dmaReadings.some(r => r.quality_flag === 'ANOMALY');
    const hasWarning = dmaReadings.some(r => r.quality_flag === 'SUSPICIOUS');
    if (hasCritical) return 'CRITICAL';
    if (hasWarning) return 'WARNING';
    return 'ACTIVE';
  };

  // Crear lista de sensores con datos de las lecturas
  const sensors = allReadings.length > 0 ? allReadings.map((r, i) => ({
    code: r.sensor_id,
    dma_id: r.dma_id,
    name: r.sensor_id,
    type: 'MULTI',
    status: r.quality_flag === 'ANOMALY' ? 'CRITICAL' : r.quality_flag === 'SUSPICIOUS' ? 'WARNING' : 'ACTIVE',
    latitude: r.latitude || (defaultDmas.find(d => d.code === r.dma_id)?.latitude || -8.12),
    longitude: r.longitude || (defaultDmas.find(d => d.code === r.dma_id)?.longitude || -79.02),
    pressure: r.pressure_mca,
    flow: r.flow_lps
  })) : defaultSensors;

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {dmas.map((dma) => {
          const dmaStatus = getDmaStatus(dma.code);
          const dmaReadings = sensorsByDma[dma.code] || [];
          const latestDmaReading = dmaReadings.length > 0 ? dmaReadings[0] : null;
          
          return (
            <div key={dma.code} className="kpi-card cursor-pointer hover:bg-gray-50 transition-colors" onClick={() => navigate(`/dmas/${dma.code}`)}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-gray-400">{dma.code}</span>
                <StatusBadge status={dmaStatus} />
              </div>
              <p className="font-semibold text-gray-800 truncate">{dma.name}</p>
              <p className="text-xs text-gray-400">{dma.district}</p>
              <div className="mt-2 flex gap-2 text-xs text-gray-500">
                <span>{dmaReadings.length} sensores</span>
              </div>
              {latestDmaReading && (
                <div className="mt-1 flex gap-3 text-xs text-gray-600">
                  <span>P: {latestDmaReading.pressure_mca} MCA</span>
                  <span>Q: {latestDmaReading.flow_lps} LPS</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="kpi-card p-1">
        <div className="h-[450px] rounded-xl overflow-hidden">
          {mapReady && (
            <MapContainer center={[-8.2000, -78.9950]} zoom={14} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
              <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              
              {/* Línea conectando sensores */}
              <Polyline 
                positions={sensors.map(s => [s.latitude, s.longitude])} 
                color="#0d6ebd" 
                weight={3} 
              />
              
              {/* Marcadores de Sensores */}
              {sensors.map((sensor, index) => (
                <Marker 
                  key={sensor.code} 
                  position={[sensor.latitude, sensor.longitude]} 
                  icon={getSensorMarkerIcon(
                    SENSOR_COLORS[index % SENSOR_COLORS.length],
                    sensor.status === 'CRITICAL'
                  )}
                >
                  <Popup>
                    <div className="text-sm">
                      <div className="flex items-center gap-2 mb-1">
                        <MapPin size={14} className="text-gray-500" />
                        <p className="font-bold text-gray-800 truncate">{sensor.name}</p>
                      </div>
                      <p className="text-xs text-gray-500 font-mono">{sensor.code}</p>
                      <StatusBadge status={sensor.status} className="mt-1" />
                      {sensor.pressure !== undefined && (
                        <div className="mt-2 text-xs text-gray-600 space-y-1">
                          <p>Presión: {sensor.pressure} MCA</p>
                          <p>Caudal: {sensor.flow} LPS</p>
                        </div>
                      )}
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          )}
        </div>
      </div>
    </div>
  );
}
