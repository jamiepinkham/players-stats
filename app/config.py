from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API
    app_name: str = "BMPL Stats API"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@stats-db:5432/players_stats"

    # Redis
    redis_url: str = "redis://stats-redis:6379/0"
    cache_ttl: int = 86400  # 24 hours

    # Celery
    celery_broker_url: str = "redis://stats-redis:6379/0"
    celery_result_backend: str = "redis://stats-redis:6379/0"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
