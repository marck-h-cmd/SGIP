import json
import csv
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from app.simulation.hydraulic_simulator import HydraulicSimulator

# Zona horaria de Perú (UTC-5)
PERU_TZ = timezone(timedelta(hours=-5))


class ScenarioGenerator:
    """Generador de escenarios enfocado en Moche"""
    
    def __init__(self):
        self.simulator = HydraulicSimulator()
        self.output_dir = "data/mock"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_moche_scenarios(self) -> Dict[str, List[Any]]:
        """Generar escenarios específicos para Moche"""
        dma_id = "DMA-MO-01"
        
        scenarios = {
            "moche_normal_day": {
                "type": "normal",
                "duration_hours": 24,
                "severity": 0.0,
                "description": "Día normal en Moche sin anomalías"
            },
            "moche_leak_event": {
                "type": "leak",
                "duration_hours": 24,
                "severity": 0.7,
                "description": "Fuga en Moche - Zona de Av. Pumacahua"
            },
            "moche_night_flow": {
                "type": "leak",
                "duration_hours": 12,
                "severity": 0.5,
                "description": "Anomalía de flujo nocturno en Moche"
            },
            "moche_pressure_drop": {
                "type": "pressure_drop",
                "duration_hours": 8,
                "severity": 0.6,
                "description": "Caída de presión en Moche - Sector Urbano"
            },
            "moche_false_positive": {
                "type": "sensor_noise",
                "duration_hours": 4,
                "severity": 0.3,
                "description": "Ruido de sensor en Moche - Falso positivo controlado"
            }
        }
        
        results = {}
        for scenario_name, params in scenarios.items():
            readings = self.simulator.generate_scenario(
                dma_id,
                params["type"],
                params["duration_hours"],
                severity=params["severity"]
            )
            results[scenario_name] = {
                "readings": readings,
                "metadata": params
            }
        
        return results
    
    def export_moche_scenarios(self) -> Dict[str, str]:
        """Exportar escenarios de Moche a CSV"""
        scenarios = self.generate_moche_scenarios()
        exported_files = {}
        
        for name, data in scenarios.items():
            readings = data["readings"]
            metadata = data["metadata"]
            
            filename = f"{name}_{datetime.now(PERU_TZ).strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = [
                    'timestamp', 'dma_id', 'dma_name', 'sensor_id',
                    'pressure_mca', 'flow_lps', 'source', 'quality_flag'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for reading in readings:
                    writer.writerow({
                        'timestamp': reading.timestamp.isoformat(),
                        'dma_id': reading.dma_id,
                        'dma_name': reading.dma_name,
                        'sensor_id': reading.sensor_id,
                        'pressure_mca': reading.pressure_mca,
                        'flow_lps': reading.flow_lps,
                        'source': reading.source,
                        'quality_flag': reading.quality_flag
                    })
            
            exported_files[name] = {
                "file": filepath,
                "metadata": metadata
            }
        
        # Generar metadata
        self._generate_moche_metadata(exported_files)
        
        return exported_files
    
    def _generate_moche_metadata(self, exported_files: Dict[str, Any]) -> None:
        """Generar metadata específica de Moche"""
        metadata = {
            "sector": "Moche",
            "dma_code": "DMA-MO-01",
            "generated_at": datetime.now(PERU_TZ).isoformat(),
            "scenarios": []
        }
        
        for name, data in exported_files.items():
            metadata["scenarios"].append({
                "name": name,
                "file": os.path.basename(data["file"]),
                "type": name.split('_')[1] if len(name.split('_')) > 1 else "unknown",
                "description": data["metadata"].get("description", ""),
                "duration_hours": data["metadata"].get("duration_hours", 0),
                "severity": data["metadata"].get("severity", 0)
            })
        
        with open(os.path.join(self.output_dir, "moche_scenarios_metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)