export type Call = {
  call_id: string;
  customer: { customer_id: string; name: string; phone: string; language: string };
  emi: { amount: number; currency: string; due_date: string; loan_account: string };
  status: string;
  stage_code: string;
  provider_call_id?: string;
  transcript: { speaker: string; text: string; timestamp_ms?: number }[];
  outcome?: { disposition?: string; summary?: string; sentiment?: string; duration_seconds?: number };
  raw_payload?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type Summary = {
  total_calls: number;
  total_amount: number;
  stages: Record<string, { count: number; amount: number }>;
};

