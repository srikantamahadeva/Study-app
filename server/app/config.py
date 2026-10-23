"""Environment-driven configuration.

No secrets are hardcoded. AI credentials come from the environment only; the
tutor reports "not configured" when they are absent.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Deployment / origin
    app_name: str = "Algo Study"
    app_origin: str = "http://localhost:8000"
    debug: bool = False

    # Database. Empty means "start an embedded PostgreSQL for development".
    database_url: str = ""

    # Private local file storage for uploads (PDFs, images, code files).
    upload_dir: str = "data/uploads"
    max_upload_mb: int = 20

    # Session auth
    session_ttl_days: int = 30
    login_max_failures: int = 10
    login_lockout_seconds: int = 300

    # OpenAI-compatible AI tutor adapter. Any provider that speaks the
    # /chat/completions shape works (OpenAI, OpenRouter, DeepSeek, Groq, ...).
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_max_context_chars: int = 24_000
    ai_timeout_seconds: float = 60.0

    @property
    def ai_configured(self) -> bool:
        return bool(self.ai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Test hook: re-read environment after tests mutate it."""
    get_settings.cache_clear()
