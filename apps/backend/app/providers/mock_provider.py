from datetime import datetime, timedelta
from typing import List, Optional
import random
import numpy as np
from app.providers.base_provider import TelemetryProvider
from app.domain.telemetry import TelemetryReading
from app.core.config import settings


class MockTelemetryProvider(TelemetryProvider):
    """Mock data provider enfocado en Moche"""
    
    def __init__(self):
        # Solo un DMA: Moche
        self.dmas = [{
            "code": "DMA-MO-01",
            "name": "Moche 01",
            "district": "Moche",
            "latitude": -8.1243,
            "longitude": -79.0142,
            "base_pressure": 55.2,
            "base_flow": 25.4,
            "population": 18000,
            "description": "Sector Moche - Zona urbana principal"
        }]
        
        self.sensors = [
            {
                "code": "SENS-MO-01-P",
                "dma_id": "DMA-MO-01",
                "name": "Sensor de Presión Moche 01",
                "type": "PRESSURE",
                "unit": "MCA",
                "status": "ACTIVE",
                "latitude": -8.1243,
                "longitude": -79.0142
            },
            {
                "code": "SENS-MO-01-F",
                "dma_id": "DMA-MO-01",
                "name": "Sensor de Caudal Moche 01",
                "type": "FLOW",
                "unit": "LPS",
                "status": "ACTIVE",
                "latitude": -8.1245,
                "longitude": -79.0140
            }
        ]
        self._current_time = datetime.utcnow()
        self._base_readings = self._generate_base_readings()
        self._leak_scenario_active = False
        self._leak_start_time = None
        self._leak_severity = 0.0
    
    def _generate_base_readings(self):
        """Generar lecturas base para Moche"""
        readings = []
        for dma in self.dmas:
            readings.append({
                "dma_id": dma["code"],
                "dma_name": dma["name"],
                "sensor_id": "SENS-MO-01-P",
                "pressure_mca": dma["base_pressure"],
                "flow_lps": dma["base_flow"],
                "source": "MOCK"
            })
        return readings
    
    def _add_daily_variation(self, value, variation_percent=0.05):
        """Agregar variación diaria realista"""
        hour = datetime.utcnow().hour
        # Patrón diario: mayor consumo durante el día, menor en la noche
        day_factor = 1.0 + 0.1 * np.sin((hour - 6) * np.pi / 12)
        random_noise = 1.0 + random.uniform(-variation_percent, variation_percent)
        return value * day_factor * random_noise
    
    def _simulate_leak(self, pressure, flow):
        """Simular efectos de una fuga"""
        if not self._leak_scenario_active:
            # Activar fuga aleatoriamente (10% de probabilidad por actualización)
            if random.random() < 0.02:  # 2% de probabilidad de iniciar fuga
                self._leak_scenario_active = True
                self._leak_start_time = datetime.utcnow()
                self._leak_severity = random.uniform(0.4, 0.9)
                print(f"🔴 FUGA DETECTADA en Moche - Severidad: {self._leak_severity:.2f}")
        
        if self._leak_scenario_active:
            # Calcular tiempo de fuga
            elapsed_minutes = (datetime.utcnow() - self._leak_start_time).total_seconds() / 60
            
            if elapsed_minutes > 60:  # Fuga dura 1 hora
                self._leak_scenario_active = False
                self._leak_start_time = None
                self._leak_severity = 0.0
                print("✅ Fuga resuelta en Moche")
                return pressure, flow
            
            # Efectos progresivos de la fuga
            progress = min(1.0, elapsed_minutes / 60)
            intensity = progress * self._leak_severity
            
            # Caída de presión y aumento de caudal
            pressure_loss = min(pressure * 0.15 * intensity, 12.0)
            flow_increase = min(flow * 0.25 * intensity, 18.0)
            
            pressure -= pressure_loss
            flow += flow_increase
            
        return pressure, flow
    
    def get_latest_readings(self, dma_id: Optional[str] = None) -> List[TelemetryReading]:
        """Obtener lecturas más recientes con variaciones realistas"""
        readings = []
        
        selected_dmas = self.dmas
        if dma_id:
            selected_dmas = [d for d in self.dmas if d["code"] == dma_id]
        
        for dma in selected_dmas:
            # Agregar variaciones diarias y aleatorias
            pressure = self._add_daily_variation(dma["base_pressure"])
            flow = self._add_daily_variation(dma["base_flow"])
            
            # Simular fuga
            pressure, flow = self._simulate_leak(pressure, flow)
            
            # Determinar calidad
            quality_flag = "GOOD"
            if self._leak_scenario_active:
                quality_flag = "ANOMALY"
            elif random.random() < 0.01:  # 1% de ruido
                quality_flag = "SUSPICIOUS"
                pressure *= random.uniform(0.95, 1.05)
                flow *= random.uniform(0.95, 1.05)
            
            reading = TelemetryReading(
                timestamp=self._current_time,
                dma_id=dma["code"],
                dma_name=dma["name"],
                sensor_id="SENS-MO-01-P",
                pressure_mca=round(max(10, pressure), 1),
                flow_lps=round(max(5, flow), 1),
                source="MOCK",
                quality_flag=quality_flag
            )
            readings.append(reading)
        
        return readings
    
    def get_historical_readings(
        self,
        dma_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[TelemetryReading]:
        """Generar lecturas históricas para Moche"""
        dma = next((d for d in self.dmas if d["code"] == dma_id), None)
        if not dma:
            return []
        
        readings = []
        current_date = start_date
        interval = timedelta(minutes=15)
        count = 0
        
        while current_date <= end_date and count < limit:
            hour = current_date.hour
            day_factor = 1.0 + 0.1 * np.sin((hour - 6) * np.pi / 12)
            random_noise = 1.0 + random.uniform(-0.03, 0.03)
            
            pressure = dma["base_pressure"] * day_factor * random_noise
            flow = dma["base_flow"] * day_factor * random_noise
            
            # Simular eventos históricos
            quality = "GOOD"
            
            # Fuga simulada en un punto específico
            if (current_date - start_date).total_seconds() > 18000 and \
               (current_date - start_date).total_seconds() < 25200:  # 5-7 horas después
                pressure *= 0.8
                flow *= 1.3
                quality = "ANOMALY"
                print(f"📊 Evento histórico: Fuga en {current_date}")
            
            reading = TelemetryReading(
                timestamp=current_date,
                dma_id=dma["code"],
                dma_name=dma["name"],
                sensor_id="SENS-MO-01-P",
                pressure_mca=round(max(10, pressure), 1),
                flow_lps=round(max(5, flow), 1),
                source="MOCK",
                quality_flag=quality
            )
            readings.append(reading)
            
            current_date += interval
            count += 1
        
        return readings
    
    def get_reading_by_id(self, reading_id: int) -> Optional[TelemetryReading]:
        """Obtener lectura por ID"""
        if 1 <= reading_id <= 1000:
            dma = self.dmas[0]
            return TelemetryReading(
                timestamp=self._current_time - timedelta(minutes=random.randint(1, 60)),
                dma_id=dma["code"],
                dma_name=dma["name"],
                sensor_id="SENS-MO-01-P",
                pressure_mca=dma["base_pressure"] * (1 + random.uniform(-0.1, 0.1)),
                flow_lps=dma["base_flow"] * (1 + random.uniform(-0.1, 0.1)),
                source="MOCK",
                quality_flag="GOOD"
            )
        return None
    
    def get_dma_info(self, dma_id: str) -> Optional[dict]:
        """Obtener información del DMA"""
        dma = next((d for d in self.dmas if d["code"] == dma_id), None)
        return dma.copy() if dma else None
    
    def get_all_dmas(self) -> List[dict]:
        """Obtener todos los DMAs (solo Moche)"""
        return [d.copy() for d in self.dmas]
    
    def get_dma_stats(self, dma_id: str, period_days: int = 1) -> dict:
        """Obtener estadísticas para Moche"""
        dma = next((d for d in self.dmas if d["code"] == dma_id), None)
        if not dma:
            return {}
        
        end_date = datetime.utcnow()
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