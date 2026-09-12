from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str

    azure_speech_key: str
    azure_speech_region: str = "westeurope"

    anthropic_api_key: str
    llm_model: str = "claude-haiku-4-5-20251001"

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    webapp_base_url: str
    session_signing_secret: str


settings = Settings()
