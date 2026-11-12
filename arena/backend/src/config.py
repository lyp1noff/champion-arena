import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_FILE = os.path.join(BASE_DIR, "../.env")

load_dotenv(ENV_FILE)

POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "champ")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "service_token")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() in ("1", "true", "yes")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_REGION = os.getenv("R2_REGION", "weur")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

_INSECURE_SECRET_VALUES = {"", "secret", "service_token", "change-me", "change-me-to-a-long-random-value"}


def validate_runtime_secrets() -> None:
    """Refuse to start outside dev mode with default/example auth secrets."""
    if DEV_MODE:
        return
    insecure = [
        name
        for name, value in (("JWT_SECRET", JWT_SECRET), ("SERVICE_TOKEN", SERVICE_TOKEN))
        if value.strip() in _INSECURE_SECRET_VALUES
    ]
    if insecure:
        raise RuntimeError(f"Insecure default value for {', '.join(insecure)}; set a long random value in the env")
