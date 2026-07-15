import random
import math
from datetime import datetime, timedelta, timezone
from typing import List
from app.domain.telemetry import TelemetryReading
from app.core.config import settings

# Zona horaria de Perú (UTC-5)
PERU_TZ = timezone(timedelta(hours=-5))

class HydraulicSimulator:
    """Hydraulic simulator to generate realistic operational scenarios"""

    def __init__(self):
        # Base values for Sector Moche
        self.base_pressure = 55.2  # MCA
        self.base_flow = 25.4      # LPS

    def generate_scenario(
        self,
        dma_id: str,
        scenario_type: str,
        duration_hours: int,
        severity: float = 0.0
    ) -> List[TelemetryReading]:
        """Generate a list of telemetry readings representing a hydraulic scenario"""
        readings = []
        now = datetime.now(PERU_TZ)
        start_time = now - timedelta(hours=duration_hours)
        
        # We generate a reading every 5 minutes (12 readings per hour)
        readings_per_hour = 60 // settings.reading_interval_minutes
        intervals = duration_hours * readings_per_hour
        
        for i in range(intervals):
            current_time = start_time + timedelta(minutes=settings.reading_interval_minutes * i)
            hour_of_day = current_time.hour + (current_time.minute / 60.0)
            
            # 1. Daily diurnal curve effect (diurnal consumption pattern)
            # Typically flow is low at night (2-5 AM) and peaks at morning (7-9 AM) and evening (6-8 PM)
            # Pressure behaves inversely to flow due to friction losses
            flow_diurnal_factor = 0.6 + 0.4 * math.sin((hour_of_day - 5.0) * math.pi / 12.0)
            pressure_diurnal_factor = 1.05 - 0.1 * math.sin((hour_of_day - 5.0) * math.pi / 12.0)
            
            flow = self.base_flow * flow_diurnal_factor
            pressure = self.base_pressure * pressure_diurnal_factor
            
            # Add small random noise
            flow += random.normalvariate(0, 0.2)
            pressure += random.normalvariate(0, 0.15)
            
            quality_flag = "GOOD"
            
            # 2. Scenario specific deviations
            if scenario_type == "leak":
                # A leak causes a pressure drop AND a flow increase
                flow += 12.0 * severity
                pressure -= 15.0 * severity
                quality_flag = "ANOMALY" if severity > settings.anomaly_threshold else "GOOD"
                
            elif scenario_type == "pressure_drop":
                # Supply shortage or valve closing: pressure drops, flow also drops slightly
                pressure -= 20.0 * severity
                flow -= 4.0 * severity
                quality_flag = "ANOMALY" if severity > settings.anomaly_threshold else "GOOD"
                
            elif scenario_type == "flow_surge":
                # Burst or bypass: flow spikes significantly, pressure drops slightly
                flow += 25.0 * severity
                pressure -= 5.0 * severity
                quality_flag = "ANOMALY" if severity > settings.anomaly_threshold else "GOOD"
                
            elif scenario_type == "sensor_noise":
                # Extreme spikes in pressure or flow, bad data
                if random.random() < 0.1:
                    flow += random.choice([-1.0, 1.0]) * 30.0 * severity
                    pressure += random.choice([-1.0, 1.0]) * 40.0 * severity
                    quality_flag = "BAD"

            readings.append(TelemetryReading(
                timestamp=current_time,
                dma_id=dma_id,
                dma_name=settings.target_dma_name if dma_id == settings.target_dma else "DMA-MO-02",
                sensor_id="SENS-MO-01-P" if i % 2 == 0 else "SENS-MO-01-F",
                pressure_mca=max(0.0, pressure),
                flow_lps=max(0.0, flow),
                source="simulation",
                quality_flag=quality_flag
            ))
            
        return readings
