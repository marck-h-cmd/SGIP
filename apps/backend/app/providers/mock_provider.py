from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
import random
import numpy as np
from app.providers.base_provider import TelemetryProvider
from app.domain.telemetry import TelemetryReading
from app.core.config import settings

# Zona horaria de Perú (UTC-5)
PERU_TZ = timezone(timedelta(hours=-5))


class MockTelemetryProvider(TelemetryProvider):
    """Mock data provider enfocado en Moche"""

    PRESSURE_BASELINE = 55.2  # MCA
    FLOW_BASELINE = 25.4      # LPS

    def __init__(self):
        self.dmas = [{
            "code": "DMA-MO-01",
            "name": "Moche 01",
            "district": "Moche",
            "latitude": -8.1700,
            "longitude": -79.0050,
            "base_pressure": self.PRESSURE_BASELINE,
            "base_flow": self.FLOW_BASELINE,
            "population": 18000,
            "description": "Sector Moche - Zona urbana principal"
        }]

        # Sensores posicionados entre Moche y Salaverry
        self.sensors = [
            {
                "code": "SENS-MO-01-P",
                "dma_id": "DMA-MO-01",
                "name": "Sensor de Presión Moche - Inicio",
                "type": "PRESSURE",
                "unit": "MCA",
                "status": "ACTIVE",
                "latitude": -8.1700,
                "longitude": -79.0050,
                "base_pressure": 58.5,
                "base_flow": 26.0
            },
            {
                "code": "SENS-MO-01-F",
                "dma_id": "DMA-MO-01",
                "name": "Sensor de Caudal Moche - Inicio",
                "type": "FLOW",
                "unit": "LPS",
                "status": "ACTIVE",
                "latitude": -8.1800,
                "longitude": -79.0150,
                "base_pressure": 58.2,
                "base_flow": 25.8
            },
            {
                "code": "SENS-MO-02-P",
                "dma_id": "DMA-MO-01",
                "name": "Sensor de Presión Medio 1",
                "type": "PRESSURE",
                "unit": "MCA",
                "status": "ACTIVE",
                "latitude": -8.1900,
                "longitude": -79.0100,
                "base_pressure": 55.3,
                "base_flow": 24.5
            },
            {
                "code": "SENS-MO-02-F",
                "dma_id": "DMA-MO-01",
                "name": "Sensor de Caudal Medio 1",
                "type": "FLOW",
                "unit": "LPS",
                "status": "ACTIVE",
                "latitude": -8.2000,
                "longitude": -78.9950,
                "base_pressure": 54.0,
                "base_flow": 24.3
            },
            {
                "code": "SENS-MO-03-P",
                "dma_id": "DMA-MO-01",
                "name": "Sensor de Presión Medio 2",
                "type": "PRESSURE",
                "unit": "MCA",
                "status": "ACTIVE",
                "latitude": -8.2100,
                "longitude": -78.9820,
                "base_pressure": 53.8,
                "base_flow": 25.0
            },
            {
                "code": "SENS-MO-03-F",
                "dma_id": "DMA-MO-01",
                "name": "Sensor de Caudal Salaverry - Fin",
                "type": "FLOW",
                "unit": "LPS",
                "status": "ACTIVE",
                "latitude": -8.2300,
                "longitude": -78.9700,
                "base_pressure": 52.5,
                "base_flow": 24.8
            }
        ]

        # Coordenadas de la ruta (solo sensores, de inicio a fin)
        self.route_coords = [
            [-8.1700, -79.0050],  # SENS-MO-01-P
            [-8.1800, -79.0150],  # SENS-MO-01-F
            [-8.1900, -79.0100],  # SENS-MO-02-P
            [-8.2000, -78.9950],  # SENS-MO-02-F
            [-8.2100, -78.9820],  # SENS-MO-03-P
            [-8.2300, -78.9700],  # SENS-MO-03-F
        ]
        self._base_readings = self._generate_base_readings()
        self._leak_scenario_active = False
        self._leak_start_time = None
        self._leak_severity = 0.0

        self._historical_cache: Dict[str, List[TelemetryReading]] = {}
        self._last_reading_time: Dict[str, datetime] = {}
        self._initialize_historical_cache()

    def _generate_base_readings(self):
        readings = []
        for dma in self.dmas:
            # Generar lectura base para cada sensor
            sensors = [s for s in self.sensors if s["dma_id"] == dma["code"]]
            for sensor in sensors:
                readings.append({
                    "dma_id": dma["code"],
                    "dma_name": dma["name"],
                    "sensor_id": sensor["code"],
                    "pressure_mca": dma["base_pressure"],
                    "flow_lps": dma["base_flow"],
                    "source": "MOCK"
                })
        return readings

    def _round_time(self, dt: Optional[datetime] = None) -> datetime:
        """Redondear datetime al intervalo de lectura más cercano hacia abajo"""
        if dt is None:
            dt = datetime.now(PERU_TZ)
        minute = (dt.minute // settings.reading_interval_minutes) * settings.reading_interval_minutes
        return dt.replace(minute=minute, second=0, microsecond=0)

    def _initialize_historical_cache(self):
        """Inicializar caché con 24h de datos alineados a la grilla de intervalos"""
        now = self._round_time()
        start = now - timedelta(hours=24)
        interval = timedelta(minutes=settings.reading_interval_minutes)

        for dma in self.dmas:
            dma_id = dma["code"]
            readings = []
            sensors = [s for s in self.sensors if s["dma_id"] == dma_id]
            current = start
            while current <= now:
                for sensor in sensors:
                    readings.append(self._generate_reading_at_time(dma, sensor, current))
                current += interval
            self._historical_cache[dma_id] = readings
            self._last_reading_time[dma_id] = now

    def _calculate_distance_km(self, lat1, lon1, lat2, lon2):
        """Calculate distance in km between two points using Haversine formula"""
        R = 6371.0  # Earth radius in km
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)
        a = np.sin(delta_phi / 2)**2 + \
            np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2)**2
        return R * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))

    def _generate_reading_at_time(self, dma: dict, sensor: dict, timestamp: datetime) -> TelemetryReading:
        """Generar lectura realista con patrón diario de consumo para un sensor específico"""
        hour = timestamp.hour + (timestamp.minute / 60.0)

        # Patrón diario de consumo (agua):
        #   - Mínimo nocturno ~3-5 AM (40% del caudal base)
        #   - Pico matutino ~8-9 AM
        #   - Pico vespertino ~7-8 PM
        #   - La presión varía inversamente con el caudal (~4%)
        angle = (hour - 7.0) * np.pi / 12.0
        flow_factor = 1.0 + 0.45 * np.sin(angle) + 0.10 * np.sin(2 * angle)
        pressure_factor = 1.0 - 0.04 * np.sin(angle)

        # Añadir variación entre sensores para hacerlos únicos
        sensor_offset = hash(sensor["code"]) % 100 / 1000  # Offset único por sensor
        
        raw_flow = sensor["base_flow"] * flow_factor + random.gauss(0, 0.4) + sensor_offset * 5
        raw_pressure = sensor["base_pressure"] * pressure_factor + random.gauss(0, 0.3) - sensor_offset * 3

        quality = "SUSPICIOUS" if random.random() < 0.005 else "GOOD"

        return TelemetryReading(
            timestamp=timestamp,
            dma_id=dma["code"],
            dma_name=dma["name"],
            sensor_id=sensor["code"],
            pressure_mca=round(max(25, raw_pressure), 1),
            flow_lps=round(max(8, raw_flow), 1),
            source="MOCK",
            quality_flag=quality,
            latitude=sensor["latitude"],
            longitude=sensor["longitude"]
        )

    def _simulate_leak(self, dma: dict) -> bool:
        """Activar/desactivar simulación de fuga y devolver True si está activa"""
        if not self._leak_scenario_active:
            if random.random() < 0.003:
                self._leak_scenario_active = True
                self._leak_start_time = datetime.now(PERU_TZ)
                self._leak_severity = random.uniform(0.3, 0.8)
                # Random leak location near one of the sensors or between them
                leak_sensor = random.choice([s for s in self.sensors if s["dma_id"] == dma["code"]])
                self._leak_latitude = leak_sensor["latitude"] + random.gauss(0, 0.001)
                self._leak_longitude = leak_sensor["longitude"] + random.gauss(0, 0.001)
            return False

        elapsed = (datetime.now(PERU_TZ) - self._leak_start_time).total_seconds() / 60
        if elapsed > 45:
            self._leak_scenario_active = False
            self._leak_start_time = None
            self._leak_severity = 0.0
            self._leak_latitude = None
            self._leak_longitude = None
            return False
        return True

    def get_latest_readings(self, dma_id: Optional[str] = None) -> List[TelemetryReading]:
        """Obtener última lectura de cada sensor y agregar nuevos puntos pendientes al caché"""
        current_time = self._round_time()
        interval = timedelta(minutes=settings.reading_interval_minutes)

        selected = [d for d in self.dmas if dma_id is None or d["code"] == dma_id]

        for dma in selected:
            last_time = self._last_reading_time.get(dma["code"])

            # Si no hay registro previo, usar la hora actual - 24h
            if last_time is None:
                last_time = current_time - timedelta(hours=24)

            # Obtener sensores del DMA
            sensors = [s for s in self.sensors if s["dma_id"] == dma["code"]]
            
            # Generar todos los puntos faltantes desde last_time hasta current_time
            next_time = last_time + interval
            leak_active = self._simulate_leak(dma)
            
            while next_time <= current_time:
                for sensor in sensors:
                    r = self._generate_reading_at_time(dma, sensor, next_time)
                    # Aplicar fuga a todos los sensores con un gradiente según la distancia
                    if leak_active and next_time >= self._leak_start_time:
                        elapsed = (next_time - self._leak_start_time).total_seconds() / 60
                        progress = min(1.0, elapsed / 45)
                        base_intensity = progress * self._leak_severity
                        
                        # Calculate distance from sensor to leak
                        distance = self._calculate_distance_km(
                            sensor["latitude"], sensor["longitude"],
                            self._leak_latitude, self._leak_longitude
                        )
                        
                        # Distance factor: closer sensors are more affected (inverse distance)
                        # Max effect at 0 distance, effect drops to 20% at 1km
                        distance_factor = np.exp(-distance * 5.0)  # 5.0 is a decay constant
                        intensity = base_intensity * (0.2 + 0.8 * distance_factor)
                        
                        # Apply leak effect: pressure drops, flow increases
                        new_pressure = r.pressure_mca - min(r.pressure_mca * 0.25 * intensity, 18.0)
                        new_flow = r.flow_lps + min(r.flow_lps * 0.35 * intensity, 25.0)
                        
                        # Set quality flag to ANOMALY for sensors with significant effect
                        quality_flag = "ANOMALY" if intensity > 0.15 else r.quality_flag
                        
                        r = TelemetryReading(
                            timestamp=r.timestamp,
                            dma_id=r.dma_id,
                            dma_name=r.dma_name,
                            sensor_id=sensor["code"],
                            pressure_mca=round(max(25, new_pressure), 1),
                            flow_lps=round(max(8, new_flow), 1),
                            source="MOCK",
                            quality_flag=quality_flag,
                            latitude=sensor["latitude"],
                            longitude=sensor["longitude"]
                        )
                    self._historical_cache.setdefault(dma["code"], []).append(r)
                next_time += interval

            self._last_reading_time[dma["code"]] = current_time

        # Devolver la última lectura de cada sensor
        result = []
        for dma in selected:
            cache = self._historical_cache.get(dma["code"], [])
            sensors = [s for s in self.sensors if s["dma_id"] == dma["code"]]
            # Para cada sensor, encontrar su última lectura
            for sensor in sensors:
                sensor_readings = [r for r in cache if r.sensor_id == sensor["code"]]
                if sensor_readings:
                    result.append(sensor_readings[-1])
        return result
    
    def get_historical_readings(
        self,
        dma_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[TelemetryReading]:
        """Obtener lecturas históricas del caché"""
        # Asegurar que las fechas tengan timezone
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=PERU_TZ)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=PERU_TZ)
        
        cache = self._historical_cache.get(dma_id, [])
        
        # Filtrar por rango de fechas
        filtered = [
            r for r in cache
            if start_date <= r.timestamp <= end_date
        ]
        
        return filtered[-limit:]
    
    def get_reading_by_id(self, reading_id: int) -> Optional[TelemetryReading]:
        """Obtener lectura por ID del caché"""
        cache = self._historical_cache.get("DMA-MO-01", [])
        if 0 <= reading_id < len(cache):
            return cache[reading_id]
        return None
    
    def get_dma_info(self, dma_id: str) -> Optional[dict]:
        """Obtener información del DMA"""
        dma = next((d for d in self.dmas if d["code"] == dma_id), None)
        return dma.copy() if dma else None
    
    def get_all_dmas(self) -> List[dict]:
        """Obtener todos los DMAs (solo Moche)"""
        return [d.copy() for d in self.dmas]
    
    def get_dma_stats(self, dma_id: str, period_days: int = 1) -> dict:
        """Obtener estadísticas para Moche desde el caché"""
        dma = next((d for d in self.dmas if d["code"] == dma_id), None)
        if not dma:
            return {}
        
        end_date = datetime.now(PERU_TZ)
        start_date = end_date - timedelta(days=period_days)
        readings = self.get_historical_readings(dma_id, start_date, end_date, limit=10000)
        
        if not readings:
            return {}
        
        pressures = [r.pressure_mca for r in readings]
        flows = [r.flow_lps for r in readings]
        
        # Detectar anomalías en el período
        anomalies = [r for r in readings if r.quality_flag in ["ANOMALY", "SUSPICIOUS"]]
        
        return {
            "dma_id": dma_id,
            "dma_name": dma["name"],
            "sample_count": len(readings),
            "avg_pressure": sum(pressures) / len(pressures),
            "max_pressure": max(pressures),
            "min_pressure": min(pressures),
            "avg_flow": sum(flows) / len(flows),
            "max_flow": max(flows),
            "min_flow": min(flows),
            "pressure_std": np.std(pressures),
            "flow_std": np.std(flows),
            "anomaly_count": len(anomalies),
            "anomaly_rate": len(anomalies) / len(readings) if readings else 0,
            "period_start": start_date,
            "period_end": end_date,
            "has_leak": self._leak_scenario_active
        }


# Singleton instance para mantener caché entre requests
mock_provider = MockTelemetryProvider()