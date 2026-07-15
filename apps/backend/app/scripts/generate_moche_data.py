#!/usr/bin/env python
"""
Script para generar datos mock del sector Moche
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.simulation.scenario_generator import ScenarioGenerator
from app.providers.mock_provider import MockTelemetryProvider
import json
from datetime import datetime, timedelta, timezone

# Zona horaria de Perú (UTC-5)
PERU_TZ = timezone(timedelta(hours=-5))


def generate_moche_data():
    """Generar datos completos para Moche"""
    print("🔄 Generando datos mock para el sector Moche...")
    
    # Crear proveedor
    provider = MockTelemetryProvider()
    
    # Generar escenarios
    generator = ScenarioGenerator()
    scenarios = generator.generate_moche_scenarios()
    
    # Exportar escenarios
    exported = generator.export_moche_scenarios()
    
    print(f"✅ Datos generados exitosamente para Moche")
    print(f"📁 Archivos generados: {len(exported)}")
    
    # Mostrar resumen
    for name, data in exported.items():
        print(f"  - {name}: {data['file']}")
        print(f"    Descripción: {data['metadata']['description']}")
    
    # Generar estado inicial
    initial_state = {
        "sector": "Moche",
        "dma_code": "DMA-MO-01",
        "generated_at": datetime.now(PERU_TZ).isoformat(),
        "status": "OPERATIONAL",
        "scenarios_count": len(exported),
        "sensors": [
            {
                "code": "SENS-MO-01-P",
                "type": "PRESSURE",
                "unit": "MCA",
                "status": "ACTIVE"
            },
            {
                "code": "SENS-MO-01-F",
                "type": "FLOW",
                "unit": "LPS",
                "status": "ACTIVE"
            }
        ]
    }
    
    with open("data/mock/moche_initial_state.json", 'w') as f:
        json.dump(initial_state, f, indent=2)
    
    print("\n📊 Estado inicial guardado en: data/mock/moche_initial_state.json")


if __name__ == "__main__":
    generate_moche_data()