#!/usr/bin/env python
"""
Script para inicializar el sistema con datos de Moche
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.telemetry_service import TelemetryService
from app.services.anomaly_service import AnomalyService
from app.services.incident_service import IncidentService
from app.services.kpi_service import KPIService
from app.core.config import settings
import json
from datetime import datetime


def init_moche_system():
    """Inicializar sistema con datos de Moche"""
    print("🚀 Inicializando SGIP-CAP para el sector Moche...")
    print(f"📍 DMA objetivo: {settings.target_dma}")
    
    # Inicializar servicios
    telemetry = TelemetryService()
    anomaly = AnomalyService()
    incident = IncidentService()
    kpi = KPIService()
    
    # ---------------------------------------------------------
    # DB Seeding for Moche DMA and Sensors
    # ---------------------------------------------------------
    from app.infrastructure.database import db
    from app.infrastructure.models import DMAModel, SensorModel
    
    session = db.SessionLocal()
    try:
        # Check if DMA exists
        dma = session.query(DMAModel).filter(DMAModel.code == settings.target_dma).first()
        if not dma:
            print(f"🌱 Insertando DMA {settings.target_dma} en la base de datos...")
            dma = DMAModel(
                code=settings.target_dma,
                name="Moche 01",
                district="Moche",
                latitude=-8.1243,
                longitude=-79.0142,
                status="ACTIVE",
                population=18000,
                description="Sector Moche - Zona urbana principal"
            )
            session.add(dma)
            
            # Add Sensors
            p_sensor = SensorModel(
                code="SENS-MO-01-P",
                dma_id=settings.target_dma,
                name="Sensor de Presión Moche 01",
                type="PRESSURE",
                unit="MCA",
                status="ACTIVE",
                latitude=-8.1243,
                longitude=-79.0142
            )
            f_sensor = SensorModel(
                code="SENS-MO-01-F",
                dma_id=settings.target_dma,
                name="Sensor de Caudal Moche 01",
                type="FLOW",
                unit="LPS",
                status="ACTIVE",
                latitude=-8.1245,
                longitude=-79.0140
            )
            session.add(p_sensor)
            session.add(f_sensor)
            session.commit()
            print("✅ DMA y Sensores insertados correctamente.")
        else:
            print(f"ℹ️ DMA {settings.target_dma} ya existe en la base de datos.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error insertando datos semilla: {e}")
    finally:
        session.close()
    # ---------------------------------------------------------
    
    # Obtener datos de Moche
    dma_info = telemetry.get_dma_info(settings.target_dma)
    if dma_info:
        print(f"✅ DMA encontrado: {dma_info['name']}")
        print(f"   Distrito: {dma_info['district']}")
        print(f"   Población: {dma_info.get('population', 'N/A')}")
    
    # Obtener lecturas actuales
    readings = telemetry.get_latest_readings()
    if readings:
        reading = readings[0]
        print(f"\n📊 Lectura actual:")
        print(f"   Presión: {reading.pressure_mca} MCA")
        print(f"   Caudal: {reading.flow_lps} LPS")
        print(f"   Calidad: {reading.quality_flag}")
    
    # Analizar anomalías
    print(f"\n🔍 Analizando anomalías en Moche...")
    analysis = anomaly.analyze_dma(settings.target_dma, hours=24)
    
    if analysis:
        print(f"   Total lecturas: {analysis.get('total_readings', 0)}")
        print(f"   Anomalías detectadas: {analysis.get('anomalies_detected', 0)}")
        print(f"   Tasa de anomalías: {analysis.get('anomaly_rate', 0):.2%}")
        
        if analysis.get('anomalies_detected', 0) > 0:
            print("   ⚠️ Se detectaron anomalías recientes:")
            for anomaly_data in analysis.get('anomalies', [])[:3]:
                print(f"      - Score: {anomaly_data.get('score', 0):.3f}")
                print(f"        Severidad: {anomaly_data.get('anomaly', {}).severity if anomaly_data.get('anomaly') else 'N/A'}")
    
    # Obtener KPIs ejecutivos
    print(f"\n📈 KPIs de Moche:")
    kpis = kpi.get_dma_metrics(settings.target_dma)
    
    if kpis and 'error' not in kpis:
        print(f"   Riesgo: {kpis.get('risk_level', 'N/A')}")
        print(f"   Incidentes últimos 30 días: {kpis.get('incidents_last_30_days', 0)}")
        print(f"   Pérdida estimada: {kpis.get('water_loss_estimate', 0):.2f} m³/día")
    
    print(f"\n✅ Sistema inicializado correctamente para Moche")
    print(f"📋 API disponible en: http://localhost:8000/api/docs")


if __name__ == "__main__":
    init_moche_system()