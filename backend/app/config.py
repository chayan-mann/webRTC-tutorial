from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://interview:interview@localhost:5432/interview"
    STORAGE_DIR: str = "./storage"
    CORS_ORIGIN: str = "http://localhost:5173"
    SEGMENT_SECONDS: int = 60
    STUN_URL: str = "stun:stun.l.google.com:19302"
    ICE_GATHERING_TIMEOUT: float = 5.0

    class Config:
        env_file = ".env"


settings = Settings()
