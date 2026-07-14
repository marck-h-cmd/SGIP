import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from app.domain.telemetry import TelemetryReading
from app.domain.anomaly import Anomaly, AnomalySeverity
from app.ml.feature_engineering import FeatureEngineer
from app.core.config import settings
from app.core.exceptions import MLException


class IsolationForestModel:
    """Isolation Forest model for anomaly detection"""
    
    def __init__(self):
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.threshold = settings.anomaly_threshold
        self.is_trained = False
        self.feature_columns = ['pressure_mca', 'flow_lps', 'hour', 'day_of_week']
        self.train_min_score = None
        self.train_max_score = None
    
    def train(self, readings: List[TelemetryReading]) -> None:
        """Train the Isolation Forest model"""
        try:
            if len(readings) < 100:
                raise MLException(f"Need at least 100 readings for training, got {len(readings)}")
            
            # Extract features
            X = self.feature_engineer.extract_batch_features(readings)
            
            # Train model
            self.model = IsolationForest(
                contamination=0.05,  # Expected proportion of outliers
                random_state=42,
                n_estimators=100,
                max_samples='auto',
                bootstrap=False
            )
            self.model.fit(X)
            self.is_trained = True
            
            # Calculate and store bounds for normalization
            train_decision_scores = self.model.decision_function(X)
            self.train_min_score = float(np.min(train_decision_scores))
            self.train_max_score = float(np.max(train_decision_scores))
            
        except Exception as e:
            raise MLException(f"Error training model: {str(e)}")
    
    def predict(self, reading: TelemetryReading) -> Tuple[bool, float, dict]:
        """Predict if a reading is an anomaly"""
        if not self.is_trained:
            raise MLException("Model not trained")
        
        try:
            # Extract features
            features = self.feature_engineer.extract_features(reading)
            X = np.array([list(features.values())])
            
            # Get anomaly score
            score = self._calculate_anomaly_score(X)
            
            # Determine if anomaly
            is_anomaly = score >= self.threshold
            
            # Get additional analysis
            analysis = {
                'feature_values': features,
                'score': score,
                'threshold': self.threshold,
                'is_anomaly': is_anomaly
            }
            
            return is_anomaly, score, analysis
            
        except Exception as e:
            raise MLException(f"Error making prediction: {str(e)}")
    
    def _calculate_anomaly_score(self, X: np.ndarray) -> float:
        """Calculate anomaly score (0 to 1)"""
        try:
            # Get decision function (lower = more anomalous)
            decision_scores = self.model.decision_function(X)
            
            # Normalize to [0, 1] where higher = more anomalous
            # This uses the fact that decision_function returns negative for anomalies
            min_score = self.train_min_score if self.train_min_score is not None else np.min(decision_scores)
            max_score = self.train_max_score if self.train_max_score is not None else np.max(decision_scores)
            
            if max_score > min_score:
                # Normalize so that lower scores are higher anomalies
                normalized = 1 - ((decision_scores - min_score) / (max_score - min_score))
                final_score = float(normalized[0])
                return max(0.0, min(1.0, final_score))
            else:
                return 0.5
            
        except Exception as e:
            raise MLException(f"Error calculating anomaly score: {str(e)}")
    
    def predict_batch(self, readings: List[TelemetryReading]) -> List[Tuple[bool, float]]:
        """Predict for a batch of readings"""
        if not self.is_trained:
            raise MLException("Model not trained")
        
        try:
            # Extract features
            X = self.feature_engineer.extract_batch_features(readings)
            
            # Get anomaly scores
            results = []
            for i, reading in enumerate(readings):
                is_anomaly, score, _ = self.predict(reading)
                results.append((is_anomaly, score))
            
            return results
            
        except Exception as e:
            raise MLException(f"Error making batch predictions: {str(e)}")
    
    def save_model(self, path: str) -> None:
        """Save model to disk"""
        if not self.is_trained:
            raise MLException("Cannot save untrained model")
        
        try:
            joblib.dump(self.model, path)
        except Exception as e:
            raise MLException(f"Error saving model: {str(e)}")
    
    def load_model(self, path: str) -> None:
        """Load model from disk"""
        try:
            self.model = joblib.load(path)
            self.is_trained = True
        except Exception as e:
            raise MLException(f"Error loading model: {str(e)}")
    
    def create_anomaly(
        self,
        reading: TelemetryReading,
        score: float,
        historical_avg_flow: Optional[float] = None
    ) -> Anomaly:
        """Create Anomaly domain object from prediction"""
        # Calculate changes
        pressure_change = 0.0
        flow_change = 0.0
        
        if historical_avg_flow:
            flow_change = reading.flow_lps - historical_avg_flow
        
        # Calculate severity
        severity = self.feature_engineer.calculate_anomaly_severity(
            score,
            pressure_change,
            flow_change
        )
        
        # Estimate water loss
        loss_volume = None
        if historical_avg_flow and flow_change > 0:
            loss_volume = self.feature_engineer.estimate_water_loss(
                reading,
                historical_avg_flow
            )
        
        return Anomaly(
            telemetry_id=reading.id or 0,
            dma_id=reading.dma_id,
            dma_name=reading.dma_name,
            anomaly_score=score,
            severity=severity,
            pressure_variation=pressure_change if pressure_change != 0 else None,
            flow_variation=flow_change if flow_change != 0 else None,
            estimated_loss_volume=loss_volume,
            description=f"Anomalía detectada en {reading.dma_name}: Score {score:.3f}, Severidad {severity.value}"
        )