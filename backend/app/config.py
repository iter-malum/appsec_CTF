from functools import lru_cache
from pathlib import Path
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _from_file_or_env(name: str, default: str = "") -> str:
    path = os.getenv(f"{name}_FILE")
    if path and Path(path).is_file():
        return Path(path).read_text(encoding="utf-8").strip()
    # Prefer dedicated files under /secrets when present (Docker volume)
    secrets_map = {
        "SECRET_KEY": "/secrets/secret_key",
        "ADMIN_PASSWORD": "/secrets/admin_password",
        "POSTGRES_PASSWORD": "/secrets/postgres_password",
    }
    fallback = secrets_map.get(name)
    if fallback and Path(fallback).is_file():
        return Path(fallback).read_text(encoding="utf-8").strip()
    return os.getenv(name, default).strip()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    secret_key: str = ""
    access_token_expire_minutes: int = 60 * 8  # 8 hours
    admin_username: str = "admin-ussc"
    admin_password: str = ""
    upload_dir: str = "./uploads"
    max_upload_mb: int = 25
    team_max_size: int = 10
    allowed_report_extensions: str = ".pdf,.docx,.txt,.md"
    cors_origins: str = "http://localhost:8080,https://localhost:8443,http://localhost:3000"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_name: str = "access_token"
    rate_limit_login: int = 10  # per window
    rate_limit_register: int = 5
    rate_limit_window_sec: int = 60
    environment: str = "production"

    @field_validator("secret_key")
    @classmethod
    def secret_ok(cls, v: str) -> str:
        weak = {"", "dev_secret_key_change_in_production_please", "change_me", "secret"}
        if v.strip() in weak or len(v.strip()) < 24:
            raise ValueError("SECRET_KEY must be a strong random value (len >= 24)")
        return v.strip()

    @field_validator("admin_password")
    @classmethod
    def admin_pass_ok(cls, v: str) -> str:
        weak = {"", "admin123", "password", "change_me", "change_me_admin_password"}
        if v.strip() in weak or len(v.strip()) < 12:
            raise ValueError("ADMIN_PASSWORD must be strong (len >= 12, not a default)")
        return v.strip()


@lru_cache
def get_settings() -> Settings:
    # Prefer Docker secret files when present
    secret_key = _from_file_or_env("SECRET_KEY")
    admin_password = _from_file_or_env("ADMIN_PASSWORD")
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        user = os.getenv("POSTGRES_USER", "appsec")
        password = _from_file_or_env("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST", "db")
        db = os.getenv("POSTGRES_DB", "appsec_ctf")
        if password:
            database_url = f"postgresql+psycopg://{user}:{password}@{host}:5432/{db}"

    return Settings(
        database_url=database_url or "postgresql+psycopg://appsec:invalid@db:5432/appsec_ctf",
        secret_key=secret_key,
        admin_password=admin_password,
        admin_username=os.getenv("ADMIN_USERNAME", "admin-ussc"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 8))),
        upload_dir=os.getenv("UPLOAD_DIR", "./uploads"),
        cors_origins=os.getenv(
            "CORS_ORIGINS",
            "http://localhost:8080,https://localhost:8443,http://localhost:3000",
        ),
        cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes"),
        environment=os.getenv("ENVIRONMENT", "production"),
    )
