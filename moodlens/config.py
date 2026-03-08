from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openrouter_api_key: str
    openrouter_model: str = "anthropic/claude-haiku-4-5"
    max_image_size_mb: int = 10
    output_format: str = "png"
