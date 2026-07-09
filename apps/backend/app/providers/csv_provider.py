from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
import os
from app.providers.base_provider import TelemetryProvider
from app.domain.telemetry import TelemetryReading
from app.core.exceptions import ProviderException


class CSVTelemetryProvider(TelemetryProvider):
    """CSV data provider for imported data"""
    
    def __init__(self, csv_path: str = None):
        self.csv_path = csv_path or os.getenv("CSV_DATA_PATH", "data/sedalib_imports/scada_export.csv")
        self._data = None
        self._dmas = None
        self._load_data()
    
    def _load_data(self):
        """Load and normalize CSV data"""
        try:
            if not os.path.exists(self.csv_path):
                raise ProviderException(f"CSV file not found: {self.csv_path}")
            
            df = pd.read_csv(self.csv_path)
            self._data = df
            
            # Extract DMA information
            self._dmas = []
            if 'dma_id' in df.columns:
                unique_dmas = df['dma_id'].unique()
                for dma_id in unique_dmas:
                    dma_data = df[df['dma_id'] == dma_id]
                    self._dmas.append({
                        "code": dma_id,
                        "name": dma_data['dma_name'].iloc[0] if 'dma_name' in df.columns else dma_id,
                        "district": dma_data['district'].iloc[0] if 'district' in df.columns else "Unknown",
                        "latitude": float(dma_data['latitude'].iloc[0]) if 'latitude' in df.columns else None,
                        "longitude": float(dma_data['longitude'].iloc[0]) if 'longitude' in df.columns else None
                    })
        
        except Exception as e:
            raise ProviderException(f"Error loading CSV data: {str(e)}")
    
    def _normalize_reading(self, row) -> TelemetryReading:
        """Normalize a CSV row to TelemetryReading"""
        return TelemetryReading(
            timestamp=pd.to_datetime(row.get('timestamp', datetime.utcnow())),
            dma_id=str(row.get('dma_id', 'UNKNOWN')),
            dma_name=str(row.get('dma_name', 'Unknown')),
            sensor_id=str(row.get('sensor_id', 'SENSOR-001')),
            pressure_mca=float(row.get('pressure_mca', 0.0)),
            flow_lps=float(row.get('flow_lps', 0.0)),
            source="CSV",
            quality_flag=str(row.get('quality_flag', 'GOOD')),
            temperature=float(row.get('temperature')) if 'temperature' in row and pd.notna(row.get('temperature')) else None
        )
    
    def get_latest_readings(self, dma_id: Optional[str] = None) -> List[TelemetryReading]:
        """Get latest readings from CSV"""
        if self._data is None:
            return []
        
        try:
            # Get latest timestamp for each DMA
            if dma_id:
                df_filtered = self._data[self._data['dma_id'] == dma_id]
            else:
                df_filtered = self._data
            
            if df_filtered.empty:
                return []
            
            latest_per_dma = df_filtered.groupby('dma_id').tail(1)
            readings = []
            
            for _, row in latest_per_dma.iterrows():
                readings.append(self._normalize_reading(row))
            
            return readings
        
        except Exception as e:
            raise ProviderException(f"Error getting latest readings: {str(e)}")
    
    def get_historical_readings(
        self,
        dma_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[TelemetryReading]:
        """Get historical readings from CSV"""
        if self._data is None:
            return []
        
        try:
            df_filtered = self._data[
                (self._data['dma_id'] == dma_id) &
                (pd.to_datetime(self._data['timestamp']) >= start_date) &
                (pd.to_datetime(self._data['timestamp']) <= end_date)
            ]
            
            if df_filtered.empty:
                return []
            
            df_sorted = df_filtered.sort_values('timestamp').head(limit)
            readings = []
            
            for _, row in df_sorted.iterrows():
                readings.append(self._normalize_reading(row))
            
            return readings
        
        except Exception as e:
            raise ProviderException(f"Error getting historical readings: {str(e)}")
    
    def get_reading_by_id(self, reading_id: int) -> Optional[TelemetryReading]:
        """Get reading by ID from CSV"""
        if self._data is None:
            return None
        
        try:
            if 'id' not in self._data.columns:
                return None
            
            row = self._data[self._data['id'] == reading_id]
            if row.empty:
                return None
            
            return self._normalize_reading(row.iloc[0])
        
        except Exception:
            return None
    
    def get_dma_info(self, dma_id: str) -> Optional[dict]:
        """Get DMA information from CSV"""
        dma = next((d for d in self._dmas if d["code"] == dma_id), None)
        return dma.copy() if dma else None
    
    def get_all_dmas(self) -> List[dict]:
        """Get all DMAs from CSV"""
        return [d.copy() for d in self._dmas]
    
    def get_dma_stats(self, dma_id: str, period_days: int = 1) -> dict:
        """Get statistical summary for a DMA from CSV"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        readings = self.get_historical_readings(dma_id, start_date, end_date, limit=10000)
        
        if not readings:
            return {}
        
        pressures = [r.pressure_mca for r in readings]
        flows = [r.flow_lps for r in readings]
        
        return {
            "dma_id": dma_id,
            "dma_name": readings[0].dma_name,
            "sample_count": len(readings),
            "avg_pressure": sum(pressures) / len(pressures),
            "max_pressure": max(pressures),
            "min_pressure": min(pressures),
            "avg_flow": sum(flows) / len(flows),
            "max_flow": max(flows),
            "min_flow": min(flows),
            "period_start": start_date,
            "period_end": end_date
        }