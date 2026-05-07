from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_read_dsn: str
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()