from functools import lru_cache
from pathlib import Path
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _secret(name: str) -> str:
    path = os.getenv(f"{name}_FILE")
    if path and Path(path).is_file():
        return Path(path).read_text(encoding="utf-8").strip()
    mapping = {
        "SECRET_KEY": "/secrets/secret_key",
        "ADMIN_PASSWORD": "/secrets/admin_password",
        "POSTGRES_PASSWORD": "/secrets/postgres_password",
    }
    fallback = mapping.get(name)
    if fallback and Path(fallback).is_file():
        return Path(fallback).read_text(encoding="utf-8").strip()
    return os.getenv(name, "").strip()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    secret_key: str = ""
    access_token_expire_minutes: int = 480
    admin_username: str = "admin-ussc"
    admin_password: str = ""
    upload_dir: str = "./uploads"
    max_upload_mb: int = 25
    team_max_size: int = 10
    allowed_report_extensions: str = ".pdf,.docx,.txt,.md"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_name: str = "access_token"
    rate_limit_login: int = 20
    rate_limit_register: int = 10
    rate_limit_window_sec: int = 60

    @field_validator("secret_key")
    @classmethod
    def secret_ok(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY too short (need secrets volume / init-secrets)")
        return v

    @field_validator("admin_password")
    @classmethod
    def admin_ok(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("ADMIN_PASSWORD too short (need secrets volume / init-secrets)")
        return v


@lru_cache
def get_settings() -> Settings:
    secret_key = _secret("SECRET_KEY")
    admin_password = _secret("ADMIN_PASSWORD")
    pg_password = _secret("POSTGRES_PASSWORD")
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url and pg_password:
        user = os.getenv("POSTGRES_USER", "appsec")
        host = os.getenv("POSTGRES_HOST", "db")
        db = os.getenv("POSTGRES_DB", "appsec_ctf")
        database_url = f"postgresql+psycopg://{user}:{pg_password}@{host}:5432/{db}"

    return Settings(
        database_url=database_url,
        secret_key=secret_key,
        admin_password=admin_password,
        admin_username=os.getenv("ADMIN_USERNAME", "admin-ussc"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")),
        upload_dir=os.getenv("UPLOAD_DIR", "./uploads"),
        cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes"),
    )
