from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Energy Intelligence API"
    database_url: str = "sqlite:///./energy_intel.db"
    openai_api_key: str | None = None
    news_api_key: str | None = None
    eia_api_key: str | None = None
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    cors_allow_all: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

