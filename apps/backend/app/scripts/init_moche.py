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