from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Language(StrEnum):
    en = "en"
    es = "es"
    hi = "hi"


class CallStatus(StrEnum):
    triggered = "triggered"
    completed = "completed"


class InitialMessageRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    call_id: str | None = Field(default=None, min_length=1, max_length=200)
    customer_id: str = Field(default="unknown", min_length=1, max_length=64)
    customer_name: str = Field(default="Unknown customer", min_length=1, max_length=100)
    phone: str = Field(default="unknown", min_length=1, max_length=30)
    language: Language = Language.en
    emi_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    due_date: date = Field(default_factory=date.today)
    loan_account: str = Field(default="unknown", min_length=1, max_length=64)
    mock_trigger_result: Literal["success", "failure", "timeout"] = "success"

    @model_validator(mode="before")
    @classmethod
    def accept_gnani_fields(cls, value):
        if not isinstance(value, dict):
            return value
        # Gnani agent configurations commonly put console variables under one
        # of these containers and may use camelCase or upper-case field names.
        flattened = dict(value)
        for container in ("data", "variables", "metadata", "custom_data"):
            nested = value.get(container)
            if isinstance(nested, dict):
                flattened = {**nested, **flattened}
        aliases = {
            "call_id": ("callId", "CALL_ID", "call_uuid", "session_id", "conversation_id"),
            "customer_id": ("customerId", "CUSTOMER_ID", "user_id"),
            "customer_name": ("customerName", "CUSTOMER_NAME", "name", "customer"),
            "phone": ("phoneNumber", "phone_number", "mobile", "mobile_number", "to"),
            "language": ("LANGUAGE", "preferred_language"),
            "emi_amount": ("emiAmount", "EMI_AMOUNT", "amount", "due_amount"),
            "currency": ("CURRENCY",),
            "due_date": ("dueDate", "DUE_DATE", "payment_due_date", "emi_due_date"),
            "loan_account": ("loanAccount", "LOAN_ACCOUNT", "loan_account_number", "account_id"),
        }
        for target, candidates in aliases.items():
            if flattened.get(target) in (None, ""):
                for candidate in candidates:
                    if flattened.get(candidate) not in (None, ""):
                        flattened[target] = flattened[candidate]
                        break
        if not flattened.get("phone"):
            phone_number = str(flattened.get("phone_number") or "").strip()
            country_code = str(flattened.get("country_code") or "").strip()
            if phone_number:
                flattened["phone"] = f"{country_code}{phone_number}".replace(" ", "")
        language = str(flattened.get("language", "en")).lower()
        flattened["language"] = (
            "es" if language in {"es", "spanish", "español"}
            else "hi" if language in {"hi", "hindi"}
            else "en"
        )
        flattened["currency"] = str(flattened.get("currency") or "USD").upper()
        return flattened

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
    call_id: str = Field(min_length=1, max_length=200)
    DISPOSITION: str = Field(min_length=1, max_length=100)
    transcript: list[TranscriptTurn] = Field(default_factory=list, max_length=500)
    analytics: Analytics = Field(default_factory=Analytics)
    provider_call_id: str | None = Field(default=None, max_length=200)

    @model_validator(mode="before")
    @classmethod
    def accept_gnani_fields(cls, value):
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if not normalized.get("call_id"):
            normalized["call_id"] = next(
                (
                    normalized[key]
                    for key in ("callId", "CALL_ID", "call_uuid", "session_id", "conversation_id", "provider_call_id")
                    if normalized.get(key)
                ),
                None,
            )
        if not normalized.get("DISPOSITION"):
            normalized["DISPOSITION"] = normalized.get("disposition") or normalized.get("outcome")
        if "transcript" not in normalized and "call_transcript" in normalized:
            normalized["transcript"] = normalized["call_transcript"]
        return normalized


class CallCreated(BaseModel):
    call_id: str
    status: CallStatus
    provider_call_id: str | None = None
    message: str
    initial_message: str
    mocked: bool = True


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
