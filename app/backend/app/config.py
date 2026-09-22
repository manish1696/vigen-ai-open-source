from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_PATH: str = "/data/vigen.db"
    MEDIA_ROOT: str = "/data/media"
    CREW_ENDPOINT_URL: str = "http://crew-api:8001"
    CREW_SERVICE_TOKEN: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    DEBUG: bool = False
    @property
    def cors_origins_list(self):
        return [x.strip().rstrip("/") for x in self.CORS_ORIGINS.split(",") if x.strip()]
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
Path(settings.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
