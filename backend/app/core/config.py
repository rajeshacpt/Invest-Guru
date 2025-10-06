from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = "local"
    PORT: int = 8100
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@postgres:5432/investguru"
    JWT_SECRET: str = "CHANGE_ME"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    REDIS_URL: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
