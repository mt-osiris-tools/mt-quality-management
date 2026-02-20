"""
Configuration management for Document Control Process.

Loads configuration from environment variables as specified in .env.example:
- DATABASE_URL: PostgreSQL connection string
- ENCRYPTION_KEY_LEVEL_1: AES-256 key for Internal documents
- ENCRYPTION_KEY_LEVEL_2: AES-256 key for Confidential documents
- ENCRYPTION_KEY_LEVEL_3: AES-256 key for Restricted documents
- JWT_PUBLIC_KEY: RS256 public key for JWT validation
- JWT_ALGORITHM: JWT signing algorithm (default: RS256)
- APP_ENV: Application environment (development, staging, production)
- LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
"""

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = ""
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_echo: bool = False

    # Encryption Keys (AES-256, 32 bytes each, base64 encoded)
    encryption_key_level_1: str = ""
    encryption_key_level_2: str = ""
    encryption_key_level_3: str = ""

    # JWT Authentication
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"
    jwt_audience: Optional[str] = None
    jwt_issuer: Optional[str] = None

    # Application Settings
    app_env: str = "development"
    app_name: str = "Document Control Process"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    # API Settings
    api_prefix: str = "/api/v1"
    api_title: str = "Document Control API"
    api_description: str = "ISO 27001-compliant document management system"

    # CORS Settings (development only)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: list[str] = ["*"]

    # Security Settings
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5

    # Performance Settings
    max_document_size_mb: int = 50
    search_results_limit: int = 1000
    audit_query_days_limit: int = 90

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "database_url",
        "encryption_key_level_1",
        "encryption_key_level_2",
        "encryption_key_level_3",
        "jwt_public_key",
    )
    @classmethod
    def _required_non_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Required setting is missing")
        return value


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    This is the recommended pattern for FastAPI dependency injection.

    Returns:
        Settings: Application settings loaded from environment
    """
    return Settings()


# Convenience function for non-FastAPI contexts
def load_config() -> Settings:
    """Load configuration from environment variables."""
    return get_settings()
