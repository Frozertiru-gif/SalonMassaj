import logging
import json

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, DotEnvSettingsSource, EnvSettingsSource, SettingsConfigDict

logger = logging.getLogger(__name__)


def _parse_csv_tokens(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        candidates = value
    else:
        raw_value = value.strip()
        if not raw_value:
            return []
        if raw_value.startswith("["):
            try:
                parsed_value = json.loads(raw_value)
            except json.JSONDecodeError:
                candidates = raw_value.split(",")
            else:
                if isinstance(parsed_value, list):
                    candidates = [str(item) for item in parsed_value]
                else:
                    candidates = [raw_value]
        else:
            candidates = raw_value.split(",")
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        token = item.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        cleaned.append(token)
    return cleaned


class _TokenSafeEnvSettingsSource(EnvSettingsSource):
    _token_fields = {"sys_admin_tokens", "admin_tokens"}

    def prepare_field_value(self, field_name, field, value, value_is_complex):
        if field_name in self._token_fields and isinstance(value, str):
            return value
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class _TokenSafeDotEnvSettingsSource(DotEnvSettingsSource):
    _token_fields = {"sys_admin_tokens", "admin_tokens"}

    def prepare_field_value(self, field_name, field, value, value_is_complex):
        if field_name in self._token_fields and isinstance(value, str):
            return value
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        enable_decoding=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            _TokenSafeEnvSettingsSource(settings_cls),
            _TokenSafeDotEnvSettingsSource(
                settings_cls,
                env_file=cls.model_config.get("env_file"),
                env_file_encoding=cls.model_config.get("env_file_encoding"),
            ),
            file_secret_settings,
        )

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
    backup_enabled: bool = False
    backup_chat_id: int | None = None
    backup_dir: str = "/app/backups"
    backup_script_path: str = "/app/scripts/backup_db.sh"
    backup_env_path: str = "/app/scripts/backup.env"
    backup_passphrase: str | None = None
    restore_max_mb: int = 200
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

    @field_validator("backup_chat_id", mode="before")
    @classmethod
    def _normalize_backup_chat_id(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            return stripped
        return value

    @model_validator(mode="after")
    def _validate_backup_configuration(self) -> "Settings":
        if self.backup_enabled and self.backup_chat_id is None:
            raise ValueError("BACKUP_CHAT_ID must be configured when BACKUP_ENABLED=true")
        return self

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
