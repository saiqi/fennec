from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str
    DB_URI: str
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_IN_MINUTES: int = 30
    SENTRY_DSN: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None


settings = Settings()  # pyright: ignore
