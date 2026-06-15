from functools import lru_cache
from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "dev"
    app_name: str = "Agent Approvals Backend API"
    api_v1_prefix: str = "/api/v1"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24
    cors_allow_origins: str = ""
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "aa_dev"
    mongo_mock: bool = False
    mail_transport: str = ""
    resend_api_key: str = ""
    mail_from: str = "aa@iamt12e.co.zw"
    mail_host: str = "localhost"
    mail_port: int = 1025
    web_push_vapid_private_key: str = ""
    web_push_vapid_public_key: str = ""
    web_push_subject: str = ""
    web_app_url: str = "http://localhost:3000"
    password_reset_token_expires_minutes: int = 60

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "dev")
    env_file = BASE_DIR / f".env.{app_env}"
    if env_file.exists():
        return Settings(_env_file=env_file)
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
