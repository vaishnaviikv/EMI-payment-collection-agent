"""Seed Atlas with safe, fictional EMI Flow demonstration records.

Run from the backend directory:
    .venv/bin/python scripts/seed_demo.py
"""

import asyncio
from datetime import datetime, timedelta, timezone

from bson.decimal128 import Decimal128
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.repository import CallRepository

NOW = datetime.now(timezone.utc)


def record(index, *, customer_id, name, phone, language, amount, due_date, loan_account, stage_code, summary, disposition, transcript, duration):
    created = NOW - timedelta(hours=index + 1)
    return {
        "call_id": f"demo-call-{index:03d}",
        "provider_call_id": f"mock-demo-{index:03d}",
        "customer": {"customer_id": customer_id, "name": name, "phone": phone, "language": language},
        "emi": {"amount": Decimal128(str(amount)), "currency": "USD", "due_date": due_date, "loan_account": loan_account},
        "status": "completed" if stage_code != "pending_call" else "triggered",
        "stage_code": stage_code,
        "webhook_ids": [f"demo-webhook-{index:03d}"] if stage_code != "pending_call" else [],
        "transcript": transcript,
        "outcome": {"disposition": disposition, "summary": summary, "sentiment": "neutral", "duration_seconds": duration} if stage_code != "pending_call" else None,
        "raw_payload": {"demo": True, "DISPOSITION": disposition} if stage_code != "pending_call" else None,
        "created_at": created,
        "updated_at": created + timedelta(minutes=2),
    }


DEMO_CALLS = [
    record(1, customer_id="CUS-1042", name="Maya Rivera", phone="+14155550184", language="en", amount=250, due_date="2026-07-30", loan_account="LN-84021", stage_code="PTP_FUTURE", disposition="PTP_FUTURE", summary="Customer committed to pay on July 30.", duration=52, transcript=[{"speaker": "agent", "text": "May I confirm I am speaking with the account holder?"}, {"speaker": "customer", "text": "Yes. I will pay on July 30."}]),
    record(2, customer_id="CUS-1098", name="Daniel Chen", phone="+14155550129", language="en", amount=310, due_date="2026-07-28", loan_account="LN-84116", stage_code="ALREADY_PAID", disposition="ALREADY_PAID", summary="Customer reports that payment was already completed.", duration=38, transcript=[{"speaker": "customer", "text": "I paid it through the app this morning."}]),
    record(3, customer_id="CUS-1120", name="Sofia Martinez", phone="+14155550177", language="es", amount=180, due_date="2026-08-01", loan_account="LN-84203", stage_code="CALLBACK_SCHEDULED", disposition="CALLBACK_SCHEDULED", summary="Customer requested a callback tomorrow after 6 PM.", duration=44, transcript=[{"speaker": "customer", "text": "Puede llamarme manana despues de las seis."}]),
    record(4, customer_id="CUS-1165", name="Noah Williams", phone="+14155550163", language="en", amount=420, due_date="2026-07-29", loan_account="LN-84289", stage_code="RNR", disposition="RNR", summary="No customer response after the call connected.", duration=24, transcript=[]),
    record(5, customer_id="CUS-1179", name="Aarav Patel", phone="+14155550160", language="en", amount=275, due_date="2026-08-05", loan_account="LN-84311", stage_code="pending_call", disposition="PENDING", summary="", duration=0, transcript=[]),
]


async def main():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    repository = CallRepository(client[settings.mongodb_database])
    await repository.ensure_indexes()
    for document in DEMO_CALLS:
        await repository.collection.replace_one({"call_id": document["call_id"]}, document, upsert=True)
    total = await repository.collection.count_documents({})
    client.close()
    print(f"Seeded {len(DEMO_CALLS)} fictional calls. Atlas now has {total} call records.")


if __name__ == "__main__":
    asyncio.run(main())
