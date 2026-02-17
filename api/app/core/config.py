import logging

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _parse_csv_tokens(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        candidates = value
    else:
        candidates = value.split(",")
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        token = item.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        cleaned.append(token)
    return cleaned


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
    backup_enabled: bool = True
    backup_chat_id: int | None = None
    backup_dir: str = "/app/backups"
    backup_script_path: str = "/app/scripts/backup_db.sh"
    backup_env_path: str = "/app/scripts/backup.env"
    backup_passphrase: str | None = None
    backup_cron_hour: int = 3
    backup_cron_minute: int = 15
    retention_keep: int = Field(
        default=7,
        validation_alias=AliasChoices("RETENTION_KEEP", "retention_keep"),
    )
    log_level: str = "INFO"
    sys_admin_tokens: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("SYS_ADMIN_TOKENS", "SYS_ADMIN_API_KEYS"),
    )
    admin_tokens: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ADMIN_TOKENS", "ADMIN_API_KEYS"),
    )

    @field_validator("sys_admin_tokens", "admin_tokens", mode="before")
    @classmethod
    def _normalize_tokens(cls, value: str | list[str] | None) -> list[str]:
        return _parse_csv_tokens(value)

    @model_validator(mode="after")
    def _warn_on_admin_token_overlap(self) -> "Settings":
        overlap = set(self.sys_admin_tokens).intersection(self.admin_tokens)
        if overlap:
            logger.warning(
                "ADMIN_TOKENS and SYS_ADMIN_TOKENS overlap for %d token(s); SYS_ADMIN role takes precedence.",
                len(overlap),
            )
        return self


settings = Settings()
