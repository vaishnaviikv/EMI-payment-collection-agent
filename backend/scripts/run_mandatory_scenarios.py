"""Run the FDE mandatory scenarios against a deployed EMI Flow API.

Usage:
  WEBHOOK_API_KEY=... python backend/scripts/run_mandatory_scenarios.py \
    --base-url https://emi-flow-api.onrender.com \
    --output docs/test-results/mandatory-scenarios.json
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


SCENARIOS = [
    {
        "number": 1,
        "slug": "pay-today",
        "name": "Customer commits to paying today",
        "disposition": "PTP_TODAY",
        "reason": "Customer explicitly committed to pay the full EMI today.",
        "customer": "Asha Today",
        "customer_text": "I will pay the complete amount today.",
        "analytics": {"ptp_date": "2026-07-28"},
    },
    {
        "number": 2,
        "slug": "future-ptp",
        "name": "Customer provides a future PTP date",
        "disposition": "PTP_FUTURE",
        "reason": "Customer explicitly committed to pay on 2026-08-02.",
        "customer": "Ben Future",
        "customer_text": "I can pay the full amount on August 2.",
        "analytics": {"ptp_date": "2026-08-02"},
    },
    {
        "number": 3,
        "slug": "already-paid",
        "name": "Customer states payment is already complete",
        "disposition": "ALREADY_PAID",
        "reason": "Customer stated that the EMI was paid through the mobile app.",
        "customer": "Carla Paid",
        "customer_text": "I already paid this EMI through the mobile app.",
    },
    {
        "number": 4,
        "slug": "callback",
        "name": "Customer requests a callback",
        "disposition": "CALLBACK_SCHEDULED",
        "reason": "Customer requested a callback on 2026-07-29 at 18:00.",
        "customer": "Deepak Callback",
        "customer_text": "Please call me tomorrow after six in the evening.",
        "analytics": {"callback_time": "2026-07-29T18:00:00-07:00"},
    },
    {
        "number": 5,
        "slug": "financial-hardship",
        "name": "Customer refuses due to financial difficulty",
        "disposition": "RTP_FINANCIAL",
        "reason": "Customer explicitly refused because of loss of income.",
        "customer": "Elena Hardship",
        "customer_text": "I lost my income and cannot pay this EMI.",
    },
    {
        "number": 6,
        "slug": "amount-dispute",
        "name": "Customer disputes the EMI amount",
        "disposition": "DISPUTE_CHARGES",
        "reason": "Customer disputed the stated EMI amount and requested correction.",
        "customer": "Farah Dispute",
        "customer_text": "That amount is incorrect. My EMI should be lower.",
    },
    {
        "number": 7,
        "slug": "third-party",
        "name": "A third party answers the call",
        "disposition": "THIRD_PARTY",
        "reason": "A third party answered and the account holder was unavailable.",
        "customer": "Gita Account",
        "customer_text": "I am her sister. Gita is not available right now.",
    },
    {
        "number": 8,
        "slug": "language-change",
        "name": "Customer changes language during the call",
        "disposition": "PTP_FUTURE",
        "reason": "Customer switched from English to Hindi and committed to pay on 2026-08-03.",
        "customer": "Hari Bilingual",
        "customer_text": "क्या हम हिंदी में बात कर सकते हैं? मैं तीन अगस्त को भुगतान करूँगा।",
        "analytics": {"ptp_date": "2026-08-03", "language_captured": "Hindi", "language_changed": True},
    },
    {
        "number": 9,
        "slug": "disconnected",
        "name": "Call disconnects without a clear disposition",
        "disposition": "DSCN",
        "reason": "Call disconnected before the customer expressed a clear outcome.",
        "customer": "Iris Disconnected",
        "customer_text": "Hello, I can barely hear you—",
    },
]


def send(base_url, method, path, payload=None, headers=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = Request(f"{base_url.rstrip('/')}{path}", data=body, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    webhook_key = os.environ.get("WEBHOOK_API_KEY")
    if not webhook_key:
        raise SystemExit("WEBHOOK_API_KEY is required")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    results = []
    created = {}
    for scenario in SCENARIOS:
        call_id = f"fde-{run_id}-{scenario['number']:02d}-{scenario['slug']}"
        initial = {
            "call_id": call_id,
            "customer_id": f"FDE-{scenario['number']:02d}",
            "customer_name": scenario["customer"],
            "phone": f"+14155550{scenario['number']:03d}",
            "language": "en",
            "emi_amount": 100 + scenario["number"] * 25,
            "currency": "USD",
            "due_date": "2026-08-09",
            "loan_account": f"FDE-LAN-{scenario['number']:02d}",
        }
        initial_status, initial_body = send(args.base_url, "POST", "/api/Initial_Message", initial)
        webhook = {
            "call_id": call_id,
            "provider_call_id": call_id,
            "DISPOSITION": scenario["disposition"],
            "transcript": [
                {"speaker": "agent", "text": "Hello, I am calling about your upcoming EMI."},
                {"speaker": "customer", "text": scenario["customer_text"]},
            ],
            "analytics": {
                "summary": scenario["name"],
                "duration_seconds": 30 + scenario["number"],
                "disposition_reason": scenario["reason"],
                "language_captured": "English",
                **scenario.get("analytics", {}),
            },
        }
        event_id = f"fde-{run_id}-event-{scenario['number']:02d}"
        webhook_status, webhook_body = send(
            args.base_url,
            "POST",
            "/api/v1/webhooks/post-call",
            webhook,
            {"X-Webhook-API-Key": webhook_key, "X-Webhook-Id": event_id},
        )
        detail_status, detail = send(args.base_url, "GET", f"/api/calls/{call_id}")
        passed = (
            initial_status == 201
            and webhook_status == 200
            and detail_status == 200
            and detail.get("stage_code") == scenario["disposition"]
            and detail.get("outcome", {}).get("disposition_reason") == scenario["reason"]
        )
        results.append({
            "scenario": scenario["number"],
            "name": scenario["name"],
            "call_id": call_id,
            "expected_stage": scenario["disposition"],
            "actual_stage": detail.get("stage_code"),
            "disposition_reason": detail.get("outcome", {}).get("disposition_reason"),
            "status": "PASS" if passed else "FAIL",
            "http": {"initial": initial_status, "webhook": webhook_status, "detail": detail_status},
        })
        created[scenario["number"]] = (call_id, webhook, event_id)

    call_id, webhook, event_id = created[1]
    duplicate_status, duplicate_body = send(
        args.base_url,
        "POST",
        "/api/v1/webhooks/post-call",
        webhook,
        {"X-Webhook-API-Key": webhook_key, "X-Webhook-Id": event_id},
    )
    results.append({
        "scenario": 10,
        "name": "Duplicate post-call webhook is received",
        "call_id": call_id,
        "expected": "duplicate",
        "actual": duplicate_body.get("status"),
        "status": "PASS" if duplicate_status == 200 and duplicate_body.get("status") == "duplicate" else "FAIL",
        "http": {"duplicate_webhook": duplicate_status},
    })

    invalid_status, invalid_body = send(
        args.base_url,
        "POST",
        "/api/Initial_Message",
        {"customer_id": "X", "customer_name": "", "emi_amount": -1},
    )
    results.append({
        "scenario": 11,
        "name": "Invalid initial call request is submitted",
        "expected": 422,
        "actual": invalid_status,
        "status": "PASS" if invalid_status == 422 else "FAIL",
        "error": invalid_body.get("error", {}).get("code"),
    })

    for result_type, expected_http, suffix in (("failure", 502, "failure"), ("timeout", 504, "timeout")):
        failure_status, failure_body = send(
            args.base_url,
            "POST",
            "/api/Initial_Message",
            {
                "customer_id": f"FDE-12-{suffix}",
                "customer_name": "Trigger Failure Test",
                "phone": "+14155550999",
                "emi_amount": 250,
                "due_date": "2026-08-09",
                "loan_account": f"FDE-FAIL-{suffix}",
                "mock_trigger_result": result_type,
            },
        )
        results.append({
            "scenario": f"12-{suffix}",
            "name": f"Gnani Console trigger {suffix}",
            "expected": expected_http,
            "actual": failure_status,
            "call_id": failure_body.get("error", {}).get("call_id"),
            "status": "PASS" if failure_status == expected_http else "FAIL",
            "error": failure_body.get("error", {}).get("code"),
        })

    report = {
        "run_id": run_id,
        "base_url": args.base_url,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "passed": sum(row["status"] == "PASS" for row in results),
            "failed": sum(row["status"] == "FAIL" for row in results),
            "checks": len(results),
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["summary"]))
    if report["summary"]["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
