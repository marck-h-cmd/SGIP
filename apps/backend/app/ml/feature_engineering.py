import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.domain.telemetry import TelemetryReading
from app.domain.anomaly import Anomaly, AnomalySeverity


class FeatureEngineer:
    """Feature engineering for anomaly detection"""
    
    def __init__(self):
        self.feature_names = []
    
    def extract_features(self, reading: TelemetryReading) -> Dict[str, float]:
        """Extract features from a single reading"""
        features = {
            'pressure_mca': reading.pressure_mca,
            'flow_lps': reading.flow_lps,
            'hour': reading.timestamp.hour,
            'day_of_week': reading.timestamp.weekday(),
            'is_weekend': 1 if reading.timestamp.weekday() >= 5 else 0,
        }
        return features
    
    def extract_batch_features(self, readings: List[TelemetryReading]) -> np.ndarray:
        """Extract features from a batch of readings"""
        features_list = []
        
        for reading in readings:
            features = self.extract_features(reading)
            features_list.append(list(features.values()))
        
        return np.array(features_list)
    
    def calculate_statistical_features(self, readings: List[TelemetryReading]) -> Dict[str, float]:
        """Calculate statistical features from a batch of readings"""
        if not readings:
            return {}
        
        pressures = [r.pressure_mca for r in readings]
        flows = [r.flow_lps for r in readings]
        
        return {
            'pressure_mean': np.mean(pressures),
            'pressure_std': np.std(pressures),
            'pressure_min': np.min(pressures),
            'pressure_max': np.max(pressures),
            'flow_mean': np.mean(flows),
            'flow_std': np.std(flows),
            'flow_min': np.min(flows),
            'flow_max': np.max(flows),
            'pressure_range': np.max(pressures) - np.min(pressures),
            'flow_range': np.max(flows) - np.min(flows),
            'pressure_cv': np.std(pressures) / (np.mean(pressures) + 1e-6),
            'flow_cv': np.std(flows) / (np.mean(flows) + 1e-6),
        }
    
    def detect_rapid_changes(self, readings: List[TelemetryReading]) -> Dict[str, float]:
        """Detect rapid changes in readings"""
        if len(readings) < 2:
            return {}
        
        pressures = [r.pressure_mca for r in readings]
        flows = [r.flow_lps for r in readings]
        
        pressure_diffs = np.diff(pressures)
        flow_diffs = np.diff(flows)
        
        return {
            'max_pressure_change': np.max(np.abs(pressure_diffs)) if len(pressure_diffs) > 0 else 0,
            'mean_pressure_change': np.mean(np.abs(pressure_diffs)) if len(pressure_diffs) > 0 else 0,
            'max_flow_change': np.max(np.abs(flow_diffs)) if len(flow_diffs) > 0 else 0,
            'mean_flow_change': np.mean(np.abs(flow_diffs)) if len(flow_diffs) > 0 else 0,
            'pressure_derivative_max': np.max(pressure_diffs) if len(pressure_diffs) > 0 else 0,
            'flow_derivative_max': np.max(flow_diffs) if len(flow_diffs) > 0 else 0,
        }
    
    def calculate_anomaly_severity(
        self,
        anomaly_score: float,
        pressure_change: float,
        flow_change: float
    ) -> AnomalySeverity:
        """Calculate severity based on anomaly score and changes"""
        # Base severity on anomaly score
        if anomaly_score >= 0.9:
            base_severity = AnomalySeverity.CRITICAL
        elif anomaly_score >= 0.75:
            base_severity = AnomalySeverity.HIGH
        elif anomaly_score >= 0.5:
            base_severity = AnomalySeverity.MEDIUM
        else:
            base_severity = AnomalySeverity.LOW
        
        # Adjust based on actual changes
        if base_severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]:
            # Confirm with physical changes
            if abs(pressure_change) > 10 or abs(flow_change) > 15:
                return AnomalySeverity.CRITICAL
            elif abs(pressure_change) > 5 or abs(flow_change) > 8:
                return AnomalySeverity.HIGH
        
        return base_severity
    
    def estimate_water_loss(
        self,
        reading: TelemetryReading,
        historical_avg_flow: float,
        duration_minutes: int = 60
    ) -> float:
        """Estimate water loss volume in cubic meters"""
        if historical_avg_flow <= 0:
            return 0.0
        
        # Convert LPS to m³/h
        flow_increase = max(0, reading.flow_lps - historical_avg_flow)
        # Duration in hours
        duration_hours = duration_minutes / 60
        # Volume in cubic meters
        volume_lost = (flow_increase * 3600 * duration_hours) / 1000
        
        return round(volume_lost, 2)