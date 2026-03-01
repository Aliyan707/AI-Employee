"""
config.py — Application configuration using pydantic-settings.

Loads all environment variables with type validation.
Provides a cached singleton via get_settings().
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application settings loaded from environment variables or .env file.
    Missing required variables raise ValidationError with field names.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- OpenAI ---
    openai_api_key: str = Field(..., description="OpenAI API key")

    # --- Gmail ---
    gmail_credentials_path: str = Field(
        default="/secrets/gmail-credentials.json",
        description="Path to Google service account JSON credentials",
    )
    gmail_topic_name: str = Field(
        default="",
        description="Gmail PubSub topic name for push notifications",
    )
    gmail_support_address: str = Field(
        default="",
        description="Gmail address that receives customer support emails",
    )

    # --- Twilio / WhatsApp ---
    twilio_account_sid: str = Field(default="", description="Twilio Account SID")
    twilio_auth_token: str = Field(default="", description="Twilio Auth Token")
    twilio_whatsapp_from: str = Field(
        default="",
        description="Twilio WhatsApp sender number (format: whatsapp:+14155238886)",
    )

    # --- PostgreSQL ---
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="cs_fte", description="PostgreSQL database name")
    postgres_user: str = Field(
        default="cs_fte_user", description="PostgreSQL username"
    )
    postgres_password: str = Field(
        default="change_me_in_production", description="PostgreSQL password"
    )

    # --- Kafka ---
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Comma-separated Kafka broker addresses",
    )

    # --- Application ---
    secret_key: str = Field(
        default="change_me_to_a_random_32_char_string",
        description="Application secret key",
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )
    daily_report_hour: int = Field(
        default=7,
        ge=0,
        le=23,
        description="Hour (UTC) to run daily report generation",
    )

    # --- Escalation ---
    escalation_queue_webhook: str = Field(
        default="",
        description="Webhook URL for escalation notifications",
    )

    @property
    def database_url(self) -> str:
        """Async PostgreSQL connection URL for SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync PostgreSQL connection URL (for migrations)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @field_validator("daily_report_hour")
    @classmethod
    def validate_report_hour(cls, v: int) -> int:
        if not 0 <= v <= 23:
            raise ValueError("daily_report_hour must be between 0 and 23")
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached singleton for application settings.
    Call this function anywhere in the application to access config.

    Usage:
        from config import get_settings
        settings = get_settings()
        print(settings.openai_api_key)
    """
    return Settings()
