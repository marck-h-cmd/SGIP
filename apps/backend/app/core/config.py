from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://sgip_user:sgip_pass@localhost:5432/sgip_cap"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Data Provider
    data_provider: str = "mock"  # mock, csv, scada
    csv_data_path: str = "data/sedalib_imports/scada_export.csv"
    
    # ML Configuration
    anomaly_threshold: float = 0.75
    training_window_days: int = 30
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Logging
    log_level: str = "INFO"
    
    # Sector específico para MVP
    target_dma: str = "DMA-MO-01"  # Enfocado en Moche
    target_dma_name: str = "Moche 01"
    
    # Intervalo de lecturas de presión y caudal (minutos)
    reading_interval_minutes: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()