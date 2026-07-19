from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from app.providers.base_provider import TelemetryProvider
from app.providers.mock_provider import MockTelemetryProvider, mock_provider
from app.providers.csv_provider import CSVTelemetryProvider
from app.providers.scada_export_provider import SCADAExportProvider
from app.domain.telemetry import TelemetryReading
from app.core.config import settings

# Zona horaria de Perú (UTC-5)
PERU_TZ = timezone(timedelta(hours=-5))


class TelemetryService:
    """Service for handling telemetry data - Enfocado en Moche"""
    
    def __init__(self):
        self.provider = self._get_provider()
        self.target_dma = settings.target_dma
    
    def _get_provider(self) -> TelemetryProvider:
        """Get the appropriate data provider"""
        provider_type = settings.data_provider.lower()
        
        if provider_type == "mock":
            return mock_provider  # Usar singleton
        elif provider_type == "csv":
            return CSVTelemetryProvider(settings.csv_data_path)
        elif provider_type == "scada":
            return SCADAExportProvider(settings.csv_data_path)
        else:
            return mock_provider  # Usar singleton
    
    def get_latest_readings(self, dma_id: Optional[str] = None) -> List[TelemetryReading]:
        """Get latest readings - siempre enfocado en Moche si no se especifica"""
        if dma_id is None:
            dma_id = self.target_dma
        return self.provider.get_latest_readings(dma_id)
    
    def get_historical_readings(
        self,
        dma_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[TelemetryReading]:
        """Get historical readings"""
        return self.provider.get_historical_readings(dma_id, start_date, end_date, limit)
    
    def get_dma_info(self, dma_id: str) -> Optional[dict]:
        """Get DMA information"""
        return self.provider.get_dma_info(dma_id)
    
    def get_all_dmas(self) -> List[dict]:
        """Get all DMAs (solo Moche en MVP)"""
        dmas = self.provider.get_all_dmas()
        # Filtrar para solo mostrar Moche
        return [d for d in dmas if d["code"] == self.target_dma]
    
    def get_dma_summary(self, dma_id: str) -> Dict[str, Any]:
        """Get summary for Moche"""
        dma_info = self.get_dma_info(dma_id)
        if not dma_info:
            return {}
        
        latest_readings = self.get_latest_readings(dma_id)
        latest = latest_readings[0] if latest_readings else None
        
        stats = self.provider.get_dma_stats(dma_id, 1)
        
        return {
            "dma_id": dma_id,
            "dma_name": dma_info.get("name", "Moche 01"),
            "district": dma_info.get("district", "Moche"),
            "latitude": dma_info.get("latitude", -8.1243),
            "longitude": dma_info.get("longitude", -79.0142),
            "population": dma_info.get("population", 18000),
            "current_reading": latest,
            "statistics": stats,
            "status": self._determine_status(latest, stats),
            "description": dma_info.get("description", "Sector Moche - Zona urbana principal")
        }
    
    def _determine_status(self, latest: Optional[TelemetryReading], stats: dict) -> str:
        """Determine DMA status"""
        if not latest:
            return "UNKNOWN"
        
        # Verificar si hay fuga activa
        if latest.quality_flag == "ANOMALY":
            return "CRITICAL"
        
        # Verificar desviaciones
        if stats:
            pressure_mean = stats.get("avg_pressure", 0)
            flow_mean = stats.get("avg_flow", 0)
            
            pressure_deviation = abs(latest.pressure_mca - pressure_mean) / (pressure_mean + 1e-6)
            flow_deviation = abs(latest.flow_lps - flow_mean) / (flow_mean + 1e-6)
            
            if pressure_deviation > 0.2 or flow_deviation > 0.2:
                return "WARNING"
            elif pressure_deviation > 0.15 or flow_deviation > 0.15:
                return "SUSPICIOUS"
        
        return "NORMAL"
    
    def get_moche_trends(self, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """Get trends specifically for Moche"""
        return self.get_dma_trends(self.target_dma, hours)
    
    def get_dma_trends(self, dma_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get pressure and flow trends grouped by sensor"""
        end_date = datetime.now(PERU_TZ)
        start_date = end_date - timedelta(hours=hours)

        readings = self.get_historical_readings(dma_id, start_date, end_date)
        
        # Obtener sensores del provider
        sensors = []
        if hasattr(self.provider, 'sensors'):
            sensors = [s for s in self.provider.sensors if s["dma_id"] == dma_id]
        
        # Agrupar lecturas por sensor
        readings_by_sensor: Dict[str, List[TelemetryReading]] = {}
        for reading in readings:
            if reading.sensor_id not in readings_by_sensor:
                readings_by_sensor[reading.sensor_id] = []
            readings_by_sensor[reading.sensor_id].append(reading)
        
        # Preparar datos por sensor
        sensors_data = []
        for sensor in sensors:
            sensor_readings = readings_by_sensor.get(sensor["code"], [])
            pressure_data = []
            flow_data = []
            
            for reading in sensor_readings:
                pressure_data.append({
                    "timestamp": reading.timestamp.isoformat(),
                    "value": reading.pressure_mca,
                    "quality": reading.quality_flag
                })
                flow_data.append({
                    "timestamp": reading.timestamp.isoformat(),
                    "value": reading.flow_lps,
                    "quality": reading.quality_flag
                })
            
            sensors_data.append({
                "sensor_id": sensor["code"],
                "sensor_name": sensor["name"],
                "sensor_type": sensor["type"],
                "latitude": sensor["latitude"],
                "longitude": sensor["longitude"],
                "pressure": pressure_data,
                "flow": flow_data
            })

        # Also return old structure for backward compatibility (uses first sensor)
        pressure_data_old = []
        flow_data_old = []
        if len(sensors_data) > 0:
            pressure_data_old = sensors_data[0]["pressure"]
            flow_data_old = sensors_data[0]["flow"]

        return {
            "dma_id": dma_id,
            "dma_name": readings[0].dma_name if readings else "Moche 01",
            "sensors": sensors_data,
            "pressure": pressure_data_old,
            "flow": flow_data_old
        }