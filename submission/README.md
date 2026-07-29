# EMI Flow FDE Submission Evidence

This folder contains evidence and supporting artifacts for the EMI Payment Collection Agent demonstration.

## Submission report

- `EMI_Flow_FDE_Submission.pdf` — final 21-page submission report covering architecture, demonstration expectations, all mandatory scenarios, acceptance criteria, bonus items, failure handling, production readiness, limitations, and embedded evidence.
- `EMI_Flow_FDE_Submission.docx` — editable source for the report.
- `build_submission_pdf.py` — reproducible report generator.

## Gnani agent

- Agent name: EMI Payment Collection Agent
- Agent ID: `bce1ae6dde324dca8aba045f2c86f1fc`
- Live conversation ID: `9b8a1885-efd3-4d9a-9fdc-367de019e116`

## Agent-console evidence

| File | Evidence shown |
| --- | --- |
| `evidence/agent-console/01-agent-details-language-switch.png` | Agent languages, region, time zone, agent description, and language-switch threshold |
| `evidence/agent-console/02-evon-llm-settings.png` | Gnani Evon v2.0 Fast LLM configuration |
| `evidence/agent-console/03-timbre-voice-settings.png` | Gnani Timbre G v1.0 TTS with the Jenny voice; this was the only TTS model available in this Agent Console account |
| `evidence/agent-console/04-analytics-extraction-fields.png` | Structured post-call fields including disposition reason, summary, PTP date, callback time, and captured language |
| `evidence/agent-console/05-live-call-recording-transcript.png` | A live voice-test conversation with recording, transcript, duration, and latency |
| `evidence/agent-console/06-conversation-log-list.png` | Gnani Agent Testing conversation history |

The visible Gnani account configuration identifies the TTS model as **Timbre G v1.0**. This was the only TTS model available in my Agent Console account; Timbre 2.5 was not offered. I therefore describe the configuration I actually used and verified.

## Dashboard evidence

| File | Evidence shown |
| --- | --- |
| `evidence/dashboard/01-dashboard-overview-viji-pending.png` | Initial call request stored and visible as Pending |
| `evidence/dashboard/02-viji-pending-detail.png` | Complete initial customer/EMI payload before post-call completion |
| `evidence/dashboard/03-viji-medical-completed.png` | Completed medical-hardship outcome, transcript, stage code, summary, and verified webhook |
| `evidence/dashboard/04-search-by-customer.png` | Search by customer name |
| `evidence/dashboard/05-search-by-loan.png` | Search by loan-account number |
| `evidence/dashboard/07-promise-to-pay-filter-passed.png` | Corrected Promise-to-pay filter returning three matching completed calls |

## Call recording

- File: `recordings/9b8a1885-efd3-4d9a-9fdc-367de019e116.mp3`
- Source: Gnani Agent Console live voice test
- Conversation ID: `9b8a1885-efd3-4d9a-9fdc-367de019e116`
- Visible console duration: 1 minute 8 seconds

## Render deployment evidence

| File | Evidence shown |
| --- | --- |
| `evidence/render/01-fastapi-web-service-live.png` | Render web service for the FastAPI backend running live at `https://emi-flow-api.onrender.com` |
| `evidence/render/02-dashboard-static-site-live.png` | Successful production build and live Render deployment of the dashboard at `https://emi-flow-dashboard.onrender.com` |

The screenshots also provide deployment traceability through the visible Git commit identifiers and Render event timestamps.

Because I use Render's free tier, the services may spin down after inactivity. Before a live demonstration, I deploy the latest commit to restore a fresh live state and then refresh the dashboard; the first backend request can still take approximately 50 seconds while the service starts.

## MongoDB evidence

| File | Evidence shown |
| --- | --- |
| `evidence/mongodb/01-completed-call-document.png` | MongoDB Atlas `emi_flow.calls` collection containing a completed call with stage code, webhook delivery ID, transcript, outcome summary, disposition reason, PTP date, captured language, disposition, timestamps, and provider call ID |

This evidence demonstrates that the dashboard data is persisted in MongoDB rather than held only in frontend state.

## Mandatory-scenario evidence

| File | Evidence shown |
| --- | --- |
| `evidence/test-results/01-mandatory-scenarios-dashboard-overview.png` | Dashboard overview containing the generated records for mandatory scenarios 1–9: pay today, future PTP, already paid, callback, financial hardship, charge dispute, third party, language change, and disconnected without a clear outcome |

The screenshot visibly maps the generated test customers to their dashboard outcomes:

- Asha Today — Promise To Pay Today
- Ben Future — Promise To Pay
- Carla Paid — Already Paid
- Deepak Callback — Callback Scheduled
- Elena Hardship — Financial Hardship
- Farah Dispute — Charge Dispute
- Gita Account — Third Party
- Hari Bilingual — Promise To Pay after a language change
- Iris Disconnected — Disconnected

Scenarios 10–12 are verified through the automated scenario runner, API tests, and HTTP/log evidence because duplicate delivery, invalid input, and provider failure/timeout cannot all be represented as ordinary completed call rows.

## Demonstration workflow and account limitation

| File | Evidence shown |
| --- | --- |
| `evidence/workflow/01-create-mock-call-form.png` | Dashboard form used to submit a complete customer/EMI request to the FastAPI Initial Message endpoint in documented mock mode |
| `evidence/limitations/01-gnani-api-credits-prisma.png` | Gnani API playground showing the Prisma v2.5 speech-to-text product and its separate API credit balance |

The visible API-playground credits are not proof of available Gnani Agent Console outbound-call credits. After the Agent Console voice-call allowance was exhausted, the remaining end-to-end disposition scenarios were completed with the documented FastAPI mock-trigger and simulated post-call webhook workflow.

## Security

Screenshots and documentation must not expose webhook keys, API keys, passwords, tokens, or database connection strings. Any credential previously displayed during development should be rotated before submission.
