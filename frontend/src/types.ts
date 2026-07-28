export type Call = {
  call_id: string;
  customer: { customer_id: string; name: string; phone: string; language: string };
  emi: { amount: number; currency: string; due_date: string; loan_account: string };
  status: string;
  stage_code: string;
  provider_call_id?: string;
  transcript: { speaker: string; text: string; timestamp_ms?: number }[];
  outcome?: { disposition?: string; disposition_reason?: string; summary?: string; duration_seconds?: number };
  raw_payload?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type Summary = {
  total_calls: number;
  total_amount: number;
  stages: Record<string, { count: number; amount: number }>;
};

export type InitialCallRequest = {
  customer_id: string;
  customer_name: string;
  phone_number: string;
  country_code: string;
  loan_account_number: string;
  emi_amount: number;
  emi_due_date: string;
  preferred_language: string;
  currency: string;
};

export type InitialCallResponse = {
  call_id: string;
  provider_call_id?: string;
  status: string;
  message: string;
  initial_message: string;
  mocked: boolean;
};
