"""
File: config.py
Purpose:
    Centralize application configuration using Pydantic BaseSettings.

Key responsibilities:
    - Load environment variables from `.env` file or host environment.
    - Provide strongly typed access to database, Redis, Celery, JWT, and API keys.
    - Keep secrets and configuration out of source code.

Related modules:
    - app/db/session.py → consumes DATABASE_URL for DB engine.
    - app/tasks/celery_app.py → consumes Celery broker/result URLs.
    - app/services/nlp_sentiment.py → consumes HF_MODEL_NAME for model loading.
    - app/core/security.py → consumes JWT_SECRET_KEY and JWT_ALGORITHM.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        PROJECT_NAME (str): Display name for the project.
        DATABASE_URL (str): Connection string for PostgreSQL.
        REDIS_URL (str): Redis connection string (used for broker & cache).
        CELERY_BROKER_URL (str): Celery broker URL.
        CELERY_RESULT_BACKEND (str): Celery results backend.
        HF_MODEL_NAME (str): HuggingFace model identifier.
        SECRET_KEY (str): General secret key (deprecated in favor of JWT_SECRET_KEY).
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Default JWT expiration in minutes.

        JWT_SECRET_KEY (str): JWT signing key.
        JWT_ALGORITHM (str): Algorithm used for JWT (default HS256).
        JWT_EXP_MINUTES (int): Token expiration time in minutes.

        YOUTUBE_API_KEY (str): API key for YouTube Data API.
    """

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
        """
        Pydantic Config:
            - Loads environment variables from `.env` file.
            - Useful for local dev; `.env.example` should be tracked for reference.
        """

        env_file = ".env"  # use .env in dev/prod, keep .env.example as template


settings = Settings()
