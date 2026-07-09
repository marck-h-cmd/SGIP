from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from app.domain.telemetry import TelemetryReading


class TelemetryProvider(ABC):
    """Base interface for telemetry data providers"""
    
    @abstractmethod
    def get_latest_readings(self, dma_id: Optional[str] = None) -> List[TelemetryReading]:
        """Get latest readings for one or all DMAs"""
        pass
    
    @abstractmethod
    def get_historical_readings(
        self,
        dma_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[TelemetryReading]:
        """Get historical readings for a specific DMA"""
        pass
    
    @abstractmethod
    def get_reading_by_id(self, reading_id: int) -> Optional[TelemetryReading]:
        """Get a specific reading by ID"""
        pass
    
    @abstractmethod
    def get_dma_info(self, dma_id: str) -> Optional[dict]:
        """Get information about a DMA"""
        pass
    
    @abstractmethod
    def get_all_dmas(self) -> List[dict]:
        """Get all available DMAs"""
        pass
    
    @abstractmethod
    def get_dma_stats(self, dma_id: str, period_days: int = 1) -> dict:
        """Get statistical summary for a DMA"""
        pass