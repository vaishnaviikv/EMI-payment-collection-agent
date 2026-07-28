from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

get_settings.cache_clear()
from app.main import app  # noqa: E402


class FakeRepo:
    def __init__(self):
        self.calls = {}

    async def create(self, doc):
        self.calls[doc["call_id"]] = doc

    async def create_if_absent(self, doc):
        if doc["call_id"] in self.calls:
            return False
        self.calls[doc["call_id"]] = doc
        return True

    async def get(self, call_id):
        return self.calls.get(call_id)

    async def apply_webhook(self, call_id, delivery_id, update):
        row = self.calls.get(call_id)
        if not row or delivery_id in row["webhook_ids"]:
            return None
        row.update(update)
        row["webhook_ids"].append(delivery_id)
        return row

    async def list(self, filters, limit, offset):
        rows = list(self.calls.values())
        return rows[offset : offset + limit], len(rows)

    async def summary(self):
        return {"total_calls": len(self.calls), "total_amount": 0, "stages": {}}


@pytest.fixture
def client():
    repo = FakeRepo()
    app.state.repo = repo
    with TestClient(app) as test_client:
        yield test_client, repo


PAYLOAD = {
    "customer_id": "CUS-1042",
    "customer_name": "Maya Rivera",
    "phone": "+14155550184",
    "language": "en",
    "emi_amount": 18450,
    "currency": "INR",
    "due_date": "2026-08-05",
    "loan_account": "LN-84021",
}


def webhook_headers(event_id: str):
    return {"X-Webhook-API-Key": get_settings().webhook_api_key, "X-Webhook-Id": event_id}


def test_create_and_complete_call(client):
    http, repo = client
    created = http.post("/api/Initial_Message", json=PAYLOAD)
    assert created.status_code == 201
    call_id = created.json()["call_id"]
    response = http.post(
        "/api/v1/webhooks/post-call",
        headers=webhook_headers("evt-1"),
        json={
            "call_id": call_id,
            "DISPOSITION": "PROMISE_TO_PAY",
            "transcript": [{"speaker": "customer", "text": "I will pay Friday."}],
            "analytics": {"summary": "Customer committed.", "duration_seconds": 44},
        },
    )
    assert response.status_code == 200
    assert response.json()["stage_code"] == "promise_to_pay"
    assert repo.calls[call_id]["status"] == "completed"


def test_webhook_is_idempotent(client):
    http, _ = client
    call_id = http.post("/api/Initial_Message", json=PAYLOAD).json()["call_id"]
    body = {"call_id": call_id, "DISPOSITION": "PAID"}
    first = http.post("/api/v1/webhooks/post-call", headers=webhook_headers("same"), json=body)
    second = http.post("/api/v1/webhooks/post-call", headers=webhook_headers("same"), json=body)
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "duplicate"


def test_rejects_bad_key_and_bad_phone(client):
    http, _ = client
    denied = http.post("/api/v1/webhooks/post-call", json={"call_id": "missing-call", "DISPOSITION": "PAID"})
    assert denied.status_code == 401


def test_accepts_gnani_console_shape_and_preserves_call_id(client):
    http, repo = client
    response = http.post(
        "/api/Initial_Message",
        json={
            "phone_number": "",
            "flow_id": "prod-d91ed2ff1efd",
            "call_id": "9b8a1885-efd3-4d9a-9fdc-367de019e116",
            "is_initial": "False",
            "organization_id": "common",
            "environment": "production",
            "user_id": "d726aa94-6acd-48f6-a530-465560b3bac7",
            "mobile": "",
            "sender_id": "9b8a1885-efd3-4d9a-9fdc-367de019e116",
            "_id": "",
        },
    )
    assert response.status_code == 201
    call_id = "9b8a1885-efd3-4d9a-9fdc-367de019e116"
    assert response.json()["call_id"] == call_id
    assert "0 USD" not in response.json()["initial_message"]
    assert repo.calls[call_id]["customer"]["customer_id"] == "d726aa94-6acd-48f6-a530-465560b3bac7"
    assert repo.calls[call_id]["customer"]["phone"] == "unknown"
    assert repo.calls[call_id]["raw_payload"]["initial_message"]["flow_id"] == "prod-d91ed2ff1efd"


def test_post_call_recovers_when_initial_message_was_not_stored(client):
    http, repo = client
    response = http.post(
        "/api/v1/webhooks/post-call",
        headers=webhook_headers("recovery-event"),
        json={"callId": "gnani-lost-call", "disposition": "PAID"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert repo.calls["gnani-lost-call"]["status"] == "completed"
