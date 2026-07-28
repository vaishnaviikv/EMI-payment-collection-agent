import type { Call, Summary } from "./types";

export const demoCalls: Call[] = [
  {
    call_id: "c8fa8ce1-92bd-48c5-a413-47ab22e4c1a7",
    customer: { customer_id: "CUS-1042", name: "Maya Rivera", phone: "+14155550184", language: "en" },
    emi: { amount: 18450, currency: "INR", due_date: "2026-08-05", loan_account: "LN-84021" },
    status: "completed", stage_code: "promise_to_pay", provider_call_id: "gn-demo-4012",
    transcript: [
      { speaker: "agent", text: "Hello Maya, I’m calling about your upcoming EMI of ₹18,450.", timestamp_ms: 0 },
      { speaker: "customer", text: "Yes, I’ll complete it this Friday morning.", timestamp_ms: 4200 },
      { speaker: "agent", text: "Thank you. I’ve noted your commitment for Friday.", timestamp_ms: 8100 },
    ],
    outcome: { disposition: "PROMISE_TO_PAY", summary: "Customer committed to pay in full on Friday morning.", duration_seconds: 52 },
    raw_payload: { DISPOSITION: "PROMISE_TO_PAY", campaign: "august_emi", language: "en" },
    created_at: "2026-07-26T16:34:00Z", updated_at: "2026-07-26T16:35:02Z",
  },
  {
    call_id: "5b237b25-3283-4cc8-84c2-a31a8d7e390f",
    customer: { customer_id: "CUS-1098", name: "Daniel Chen", phone: "+14155550129", language: "en" },
    emi: { amount: 22100, currency: "INR", due_date: "2026-08-03", loan_account: "LN-84116" },
    status: "completed", stage_code: "paid",
    transcript: [{ speaker: "customer", text: "I paid it through the app a few minutes ago." }],
    outcome: { disposition: "PAID", summary: "Customer reports payment completed through mobile app.", duration_seconds: 38 },
    raw_payload: { DISPOSITION: "PAID", payment_channel: "mobile_app" },
    created_at: "2026-07-26T15:49:00Z", updated_at: "2026-07-26T15:50:11Z",
  },
  {
    call_id: "2d5f14db-7a25-4a0d-965a-b6fd3ee87a41",
    customer: { customer_id: "CUS-1120", name: "Sofia Martínez", phone: "+34915550177", language: "es" },
    emi: { amount: 12900, currency: "INR", due_date: "2026-08-07", loan_account: "LN-84203" },
    status: "completed", stage_code: "follow_up",
    transcript: [{ speaker: "customer", text: "¿Puede llamarme mañana después de las seis?" }],
    outcome: { disposition: "CALL_BACK", summary: "Requested a callback tomorrow after 6 PM.", duration_seconds: 44 },
    raw_payload: { DISPOSITION: "CALL_BACK", callback_window: "18:00-20:00" },
    created_at: "2026-07-26T14:20:00Z", updated_at: "2026-07-26T14:21:04Z",
  },
  {
    call_id: "70e47b66-d7ee-49b0-b703-60dd2ad935bd",
    customer: { customer_id: "CUS-1165", name: "Noah Williams", phone: "+14155550163", language: "en" },
    emi: { amount: 31750, currency: "INR", due_date: "2026-08-01", loan_account: "LN-84289" },
    status: "completed", stage_code: "unreachable", transcript: [],
    outcome: { disposition: "NO_ANSWER", summary: "Call rang without answer.", duration_seconds: 24 },
    raw_payload: { DISPOSITION: "NO_ANSWER" },
    created_at: "2026-07-26T13:58:00Z", updated_at: "2026-07-26T13:58:31Z",
  },
  {
    call_id: "921ec2e2-2fe2-4d7e-8ad2-e55db2e19d44",
    customer: { customer_id: "CUS-1179", name: "Aarav Patel", phone: "+919876543210", language: "en" },
    emi: { amount: 24600, currency: "INR", due_date: "2026-08-10", loan_account: "LN-84311" },
    status: "triggered", stage_code: "pending_call", transcript: [],
    created_at: "2026-07-26T13:35:00Z", updated_at: "2026-07-26T13:35:02Z",
  },
];

export const demoSummary: Summary = {
  total_calls: 128,
  total_amount: 2847500,
  stages: {
    promise_to_pay: { count: 47, amount: 986400 },
    paid: { count: 31, amount: 704800 },
    follow_up: { count: 22, amount: 502600 },
    unreachable: { count: 19, amount: 436200 },
    pending_call: { count: 9, amount: 217500 },
  },
};
