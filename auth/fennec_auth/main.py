from fastapi import FastAPI
import sentry_sdk
from fennec_auth.config import settings


sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment=settings.ENVIRONMENT,
)

app = FastAPI()
