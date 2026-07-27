import asyncio
import logging
from dataclasses import dataclass

import httpx

from .config import Settings

logger = logging.getLogger(__name__)


class GnaniError(RuntimeError):
    pass


@dataclass
class TriggerResult:
    provider_call_id: str
    mocked: bool


class GnaniClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    async def trigger(self, call_id: str, payload: dict) -> TriggerResult:
        if self.settings.gnani_mock_mode:
            logger.info("gnani_trigger_mocked", extra={"call_id": call_id})
            return TriggerResult(provider_call_id=f"mock-{call_id[:12]}", mocked=True)

        body = {
            "agent_id": self.settings.gnani_agent_id,
            "phone_number": payload["phone"],
            "language": payload["language"],
            "pre_call_variables": {
                "call_id": call_id,
                "customer_name": payload["customer_name"],
                "emi_amount": str(payload["emi_amount"]),
                "currency": payload["currency"],
                "due_date": str(payload["due_date"]),
                "loan_account": payload["loan_account"],
            },
        }
        headers = {"Authorization": f"Bearer {self.settings.gnani_api_key}"}
        timeout = httpx.Timeout(self.settings.gnani_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            for attempt in range(self.settings.gnani_max_retries + 1):
                try:
                    response = await client.post(self.settings.gnani_trigger_url, json=body, headers=headers)
                    if response.status_code >= 500 or response.status_code == 429:
                        raise httpx.HTTPStatusError("transient Gnani error", request=response.request, response=response)
                    response.raise_for_status()
                    data = response.json()
                    provider_id = data.get("call_id") or data.get("id")
                    if not provider_id:
                        raise GnaniError("Gnani response did not include a call identifier")
                    return TriggerResult(provider_call_id=str(provider_id), mocked=False)
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                    retryable = not isinstance(exc, httpx.HTTPStatusError) or exc.response.status_code >= 500 or exc.response.status_code == 429
                    if not retryable or attempt >= self.settings.gnani_max_retries:
                        raise GnaniError("Gnani call trigger failed") from exc
                    await asyncio.sleep(0.25 * (2**attempt))
        raise GnaniError("Gnani call trigger failed")

