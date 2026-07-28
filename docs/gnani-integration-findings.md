# Gnani integration: specification, observed behavior, and decision

## Executive summary

The FDE assignment's `Initial Message API` and Gnani Console's dynamic-greeting
callback are not the same contract.

- **FDE-required initiation API:** a business client sends complete customer and
  EMI information to FastAPI. FastAPI validates and stores it, prepares bot
  variables and an opening message, invokes Gnani's call-trigger API, and
  returns the initiation result.
- **Observed Gnani dynamic-greeting callback:** after a call is started manually
  in the Agents Console, Gnani sends FastAPI session metadata so it can obtain a
  greeting. The observed request did not contain the configured pre-call
  customer or EMI variables.

The recommended final design is to implement the FDE flow as the authoritative
path. The dynamic-greeting callback can remain as a compatibility/provider hook,
but it should not be treated as the source of customer and EMI data.

## FDE-required contract

The assignment says `POST /api/Initial_Message` receives customer information,
validates it, prepares the initial message and bot variables, stores the initial
status, triggers the Gnani call, and returns the initiation response.

Conceptually:

```text
Operator/application
    -> POST /api/Initial_Message with customer + EMI data
FastAPI
    -> validate and store pending call
    -> call Gnani call-trigger API with phone, bot variables, and our call_id
Gnani
    -> return provider call/session ID
FastAPI
    -> store provider ID and return call initiation result
```

The example object in the assignment should be treated as the business data
contract (request fields plus generated `initial_message`), even though it is
labelled "Suggested Response."

Recommended normalized request:

```json
{
  "customer_id": "CUST001",
  "customer_name": "Rahul Sharma",
  "phone_number": "9876543210",
  "country_code": "+91",
  "loan_account_number": "LAN123456",
  "emi_amount": 12500,
  "emi_due_date": "2026-07-25",
  "preferred_language": "Hindi"
}
```

Recommended response:

```json
{
  "call_id": "<our-stable-id>",
  "provider_call_id": "<gnani-id>",
  "status": "triggered",
  "initial_message": "Hi, am I speaking to Rahul?"
}
```

## What Gnani actually sent to the dynamic-greeting URL

Captured from Render at `2026-07-28 07:59:54 UTC`:

```json
{
  "phone_number": "",
  "flow_id": "prod-d91ed2ff1efd",
  "call_id": "9b8a1885-efd3-4d9a-9fdc-367de019e116",
  "is_initial": "False",
  "organization_id": "common",
  "environment": "production",
  "user_id": "d726aa94-6acd-48f6-a530-465560b3bac7",
  "mobile": "",
  "sender_id": "9b8a1885-efd3-4d9a-9fdc-367de019e116",
  "_id": ""
}
```

Values present:

- Gnani call/session ID
- Gnani flow ID
- organization and environment
- Gnani user ID
- sender/session ID
- blank phone fields

Values absent:

- customer name
- business customer ID
- loan account number
- EMI amount
- EMI due date
- preferred language

## Pre-call variables versus the Initial Message request

The console can hold pre-call variables and use them inside the agent prompt and
conversation. That does not imply that Gnani serializes those variables into
the dynamic-greeting HTTP request. The captured request proves that this agent
configuration did not do so.

Therefore, pre-call variables are useful to the Gnani runtime, but FastAPI
cannot depend on receiving them through this callback unless Gnani provides a
documented body-template/mapping feature and it is explicitly configured.

## Can the dashboard use only the post-call webhook?

Technically, yes: an authenticated post-call webhook can upsert a completed
record and the dashboard can display whatever fields it contains. The backend
supports this recovery behavior.

It should not be the primary architecture because:

1. It does not satisfy the FDE requirement to validate and store the request
   before initiating the call.
2. The dashboard cannot show pending/triggered calls.
3. Calls that fail, never connect, or never deliver a webhook disappear.
4. The post-call payload may omit customer and EMI fields, leaving placeholders.
5. Correlation is weaker unless the same stable `call_id` is deliberately sent
   through the complete flow.
6. There is no initiation response or provider-trigger error to audit.

Post-call upsert is therefore a resilience mechanism, not a replacement for the
Initial Message/initiation API.

## Recommended implementation plan

1. Keep `POST /api/Initial_Message` as the FDE-facing initiation endpoint.
2. Accept the assignment's field names as aliases for the internal model:
   `phone_number`, `country_code`, `loan_account_number`, `emi_due_date`, and
   `preferred_language`.
3. Generate a stable application `call_id`, validate and store the full request,
   and set status to `pending`.
4. Invoke Gnani's documented call-trigger API using the configured agent and
   workforce IDs, passing our `call_id` and the full bot-variable set.
5. Store Gnani's returned provider call ID and change status to `triggered`.
6. Keep the dynamic-greeting callback as a separate route or compatibility mode.
   It should look up the existing record by our ID/provider ID and return the
   already prepared greeting.
7. Keep the authenticated, idempotent post-call webhook to update the same
   record with disposition, transcript, and analytics.
8. Keep recovery upsert for unmatched post-call events, while logging and
   marking them as incomplete.

## Test evidence from 2026-07-28

Passed:

- enriched Initial Message request created a MongoDB record
- authenticated post-call webhook returned `200 accepted`
- disposition `PTP_FUTURE`, transcript, summary, duration, and extracted values
  were stored
- dashboard displayed the completed call and updated its totals

Not yet proven:

- actual outbound dialing from the Gnani call-trigger API
- live ASR/TTS/LLM behavior
- Gnani's exact automatic post-call JSON contract
- automatic propagation of console pre-call variables to HTTP callbacks

The earlier session-only persistence error was caused by a numeric placeholder
default that was not a `Decimal`; it is corrected in the backend model.

## Implemented mock-trigger demonstration

Until Gnani supplies the outbound trigger URL and credentials, the project uses
`GNANI_MOCK_MODE=true`:

1. The dashboard's **Create test call** form sends the full FDE-shaped request.
2. FastAPI accepts and normalizes `phone_number`, `country_code`,
   `loan_account_number`, `emi_due_date`, and `preferred_language`.
3. FastAPI validates and stores the record with `stage_code: pending_call`.
4. FastAPI returns a deterministic `mock-...` provider ID, `triggered` status,
   and the generated initial greeting.
5. The dashboard refreshes and shows the pending record.
6. An authenticated simulated post-call webhook completes the record.

This demonstrates the assignment's application, validation, persistence,
correlation, and post-call lifecycle without falsely claiming that a real Gnani
phone call was placed.
