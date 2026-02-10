from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/salon"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str | None = None
    telegram_bot_username: str | None = None
    telegram_admin_ids: str | None = None
    telegram_sys_admin_ids: str | None = None
    telegram_mode: str = "webhook"
    log_level: str = "INFO"


settings = Settings()
