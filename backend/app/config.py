import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EMI Flow API"
    app_env: str = "development"
    log_level: str = "INFO"
    mongodb_uri: str = "mongodb://unused-in-tests"
    mongodb_database: str = "collectflow"
    webhook_api_key: str = "change-me"
    gnani_mock_mode: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    gnani_disposition_map_json: str = (
        '{"PROMISE_TO_PAY":"promise_to_pay","PAID":"paid","CALL_BACK":"follow_up",'
        '"NO_ANSWER":"unreachable","REFUSED":"refused","WRONG_NUMBER":"invalid_contact"}'
    )

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        return [v.strip() for v in value.split(",")] if isinstance(value, str) else value

    @property
    def disposition_map(self) -> dict[str, str]:
        return {k.upper(): v for k, v in json.loads(self.gnani_disposition_map_json).items()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
