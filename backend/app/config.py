from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://gisuser:gispassword@postgres:5432/cadastralmap"
    SECRET_KEY: str = "yoursecretkeyhere"
    
    DATA_PROVIDER: str = "overture"
    OVERTURE_API_KEY: str = ""
    OVERTURE_TIMEOUT_SECONDS: int = 30
    OVERTURE_MAX_RETRIES: int = 3
    OVERTURE_CACHE_TTL_SECONDS: int = 86400
    
    PROCESSING_CRS: int = 32644  # UTM Zone 44N (Chennai region)

    class Config:
        env_file = ".env"

settings = Settings()
