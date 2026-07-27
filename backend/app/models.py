from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Language(StrEnum):
    en = "en"
    es = "es"


class CallStatus(StrEnum):
    pending = "pending"
    triggered = "triggered"
    completed = "completed"
    trigger_failed = "trigger_failed"


class InitialMessageRequest(BaseModel):
    customer_id: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    customer_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    language: Language = Language.en
    emi_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    due_date: date
    loan_account: str = Field(min_length=3, max_length=64)

    @field_validator("customer_name", "loan_account")
    @classmethod
    def strip_values(cls, value: str) -> str:
        return value.strip()


class TranscriptTurn(BaseModel):
    speaker: str = Field(min_length=1, max_length=30)
    text: str = Field(min_length=1, max_length=10000)
    timestamp_ms: int | None = Field(default=None, ge=0)


class Analytics(BaseModel):
    model_config = ConfigDict(extra="allow")
    summary: str | None = Field(default=None, max_length=4000)
    sentiment: str | None = Field(default=None, max_length=50)
    duration_seconds: int | None = Field(default=None, ge=0, le=86400)


class PostCallWebhook(BaseModel):
    model_config = ConfigDict(extra="allow")
    call_id: str = Field(min_length=8, max_length=100)
    DISPOSITION: str = Field(min_length=1, max_length=100)
    transcript: list[TranscriptTurn] = Field(default_factory=list, max_length=500)
    analytics: Analytics = Field(default_factory=Analytics)
    provider_call_id: str | None = Field(default=None, max_length=200)


class CallCreated(BaseModel):
    call_id: str
    status: CallStatus
    provider_call_id: str | None = None
    message: str


class CallView(BaseModel):
    call_id: str
    customer: dict
    emi: dict
    status: str
    stage_code: str
    provider_call_id: str | None = None
    transcript: list[dict] = []
    outcome: dict | None = None
    raw_payload: dict | None = None
    created_at: datetime
    updated_at: datetime
