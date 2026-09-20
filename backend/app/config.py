from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://appsec:appsec_secret_change_me@localhost:5432/appsec_ctf"
    secret_key: str = "dev_secret_key_change_in_production_please"
    access_token_expire_minutes: int = 60 * 24 * 7
    admin_username: str = "admin"
    admin_password: str = "admin123"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 25
    team_max_size: int = 10
    allowed_report_extensions: str = ".pdf,.docx,.txt,.md"


@lru_cache
def get_settings() -> Settings:
    return Settings()
