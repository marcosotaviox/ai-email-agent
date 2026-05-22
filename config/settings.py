"""Application configuration — loads from .env file."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.json"

    class Config:
        env_file = ".env"


settings = Settings()

EMAIL_CATEGORIES = [
    "Business",
    "Priority",
    "Administrative",
    "Education",
    "Newsletter",
    "Events",
]