"""Application settings with per-environment defaults (dev/test/prod).

Values are resolved in this order: environment variable > .env file >
default for the selected ENVIRONMENT.
"""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Sensible defaults per environment; explicit env vars always win.
_ENVIRONMENT_DEFAULTS: dict[str, dict[str, str]] = {
    "dev": {
        "database_url": "sqlite:////tmp/addresses.db",
        "app_log_file": "/tmp/app-logs/app.log",
    },
    "test": {
        "database_url": "sqlite:////tmp/test_addresses.db",
        "app_log_file": "/tmp/app-logs/test.log",
    },
    "prod": {
        "database_url": "sqlite:////data/addresses.db",
        "app_log_file": "/tmp/app-logs/app.log",
    },
}


class Settings(BaseSettings):
    """Environment-driven configuration for the whole application."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field("dev", pattern="^(dev|test|prod)$")
    database_url: str | None = None
    app_log_file: str | None = None
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _apply_environment_defaults(self) -> "Settings":
        """Fill unset values from the defaults of the active environment."""
        for name, value in _ENVIRONMENT_DEFAULTS[self.environment].items():
            if getattr(self, name) is None:
                setattr(self, name, value)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance for the current process."""
    return Settings()