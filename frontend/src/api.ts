import type { Call, Summary } from "./types";
import { demoCalls, demoSummary } from "./mockData";

// Local Vite uses a same-origin proxy; deployed builds set VITE_API_URL to the public API URL.
const API_URL = import.meta.env.VITE_API_URL || "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 6000);
  try {
    const response = await fetch(`${API_URL}${path}`, { ...init, signal: controller.signal });
    if (!response.ok) {
      const body = await response.json().catch(() => undefined);
      throw new Error(body?.error?.message || `API returned ${response.status}`);
    }
    return await response.json();
  } finally {
    window.clearTimeout(timer);
  }
}

export type NewCallPayload = {
  customer_id: string;
  customer_name: string;
  phone: string;
  language: "en" | "es";
  emi_amount: number;
  currency: string;
  due_date: string;
  loan_account: string;
};

export async function createCall(payload: NewCallPayload): Promise<{ call_id: string; status: string; message: string }> {
  return request("/api/Initial_Message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getDashboard(): Promise<{ calls: Call[]; summary: Summary; demo: boolean }> {
  try {
    const [calls, summary] = await Promise.all([
      request<{ items: Call[] }>("/api/calls?limit=100"),
      request<Summary>("/api/dashboard/summary"),
    ]);
    return { calls: calls.items, summary, demo: false };
  } catch {
    return { calls: demoCalls, summary: demoSummary, demo: true };
  }
}

export async function getCall(callId: string): Promise<Call> {
  return request<Call>(`/api/calls/${encodeURIComponent(callId)}`);
}
