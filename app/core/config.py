from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "YouTube Sentiment Analyzer"

    # Core env vars
    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    HF_MODEL_NAME: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # JWT
    JWT_SECRET_KEY: str = "supersecret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXP_MINUTES: int = 60

    # YouTube
    YOUTUBE_API_KEY: str

    class Config:
        env_file = ".env"  # use .env in dev/prod, keep .env.example as template

settings = Settings()
