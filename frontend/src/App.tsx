import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowUpRight, CalendarDays, ChevronRight, CircleDollarSign, Clock3, Headphones, PhoneCall, Search, ShieldCheck, Sparkles, TrendingUp, Users } from "lucide-react";
import { createCall, getDashboard } from "./api";
import type { NewCallPayload } from "./api";
import type { Call, Summary } from "./types";

const labels: Record<string, string> = {
  promise_to_pay: "Promise to pay", paid: "Paid", follow_up: "Follow-up",
  unreachable: "Unreachable", pending_call: "Pending", refused: "Refused",
  invalid_contact: "Invalid contact", needs_review: "Needs review",
  PTP_TODAY: "Promise to pay today", PTP_TOMORROW: "Promise to pay tomorrow", PTP_FUTURE: "Promise to pay", PTP_PARTIAL: "Partial payment",
  ALREADY_PAID: "Already paid", CALLBACK_SCHEDULED: "Callback scheduled", RTP_FINANCIAL: "Financial hardship", RTP_MEDICAL: "Medical hardship",
  RTP_NO_REASON: "Refused", DISPUTE_PAID: "Payment dispute", DISPUTE_CHARGES: "Charge dispute", NO_LOAN: "No loan", WRONG_NUMBER: "Wrong number",
  THIRD_PARTY: "Third party", BUSY: "Busy", RNR: "No response", VM: "Voicemail", DSCN: "Disconnected", UNCLEAR: "Unclear",
};

const money = (amount: number, currency = "USD") => new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
const maskPhone = (phone: string) => `${phone.slice(0, Math.min(3, phone.length - 4))} ••• ••${phone.slice(-2)}`;
const timeAgo = (value: string) => {
  const mins = Math.max(1, Math.round((Date.now() - new Date(value).getTime()) / 60000));
  return mins < 60 ? `${mins}m ago` : mins < 1440 ? `${Math.floor(mins / 60)}h ago` : `${Math.floor(mins / 1440)}d ago`;
};

function Logo() {
  return <div className="logo"><span className="logo-mark"><TrendingUp size={18} /></span><span>EMI <span>Flow</span></span></div>;
}

function StagePill({ stage }: { stage: string }) {
  return <span className={`pill ${stage}`}><i />{labels[stage] || stage.replaceAll("_", " ")}</span>;
}

const emptyCall: NewCallPayload = { customer_id: "", customer_name: "", phone: "", language: "en", emi_amount: 0, currency: "USD", due_date: "", loan_account: "" };

function NewCallDialog({ onClose, onCreated }: { onClose: () => Promise<void>; onCreated: () => Promise<void> }) {
  const [form, setForm] = useState<NewCallPayload>(emptyCall);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const update = <K extends keyof NewCallPayload>(key: K, value: NewCallPayload[K]) => setForm((current) => ({ ...current, [key]: value }));
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError("");
    if (!form.customer_id || !form.customer_name || !form.due_date || !form.loan_account || form.emi_amount <= 0) return setError("Complete every field with a valid EMI amount.");
    if (!/^\+[1-9]\d{7,14}$/.test(form.phone)) return setError("Use an international phone format, such as +14155550123.");
    setSubmitting(true);
    try { await createCall(form); await onCreated(); await onClose(); }
    catch (err) { setError(err instanceof Error ? err.message : "The call could not be initiated."); }
    finally { setSubmitting(false); }
  };
  return <div className="modal-backdrop" onMouseDown={() => void onClose()}><section className="call-dialog" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
    <button className="modal-close" onClick={() => void onClose()} aria-label="Close">×</button><div className="eyebrow">CALL INITIATION</div><h2>Start a collection call</h2><p>FastAPI validates the request, saves a pending record, and then triggers the Gnani agent.</p>
    <form onSubmit={submit}><div className="form-grid">
      <label>Customer name<input value={form.customer_name} onChange={(e) => update("customer_name", e.target.value)} /></label><label>Customer ID<input value={form.customer_id} onChange={(e) => update("customer_id", e.target.value)} placeholder="cust001" /></label>
      <label>Phone number<input value={form.phone} onChange={(e) => update("phone", e.target.value)} placeholder="+14155550123" /></label><label>Language<select value={form.language} onChange={(e) => update("language", e.target.value as "en" | "es")}><option value="en">English</option><option value="es">Spanish</option></select></label>
      <label>EMI amount<input type="number" min="0.01" step="0.01" value={form.emi_amount || ""} onChange={(e) => update("emi_amount", Number(e.target.value))} /></label><label>Due date<input type="date" value={form.due_date} onChange={(e) => update("due_date", e.target.value)} /></label>
      <label className="full">Loan account reference<input value={form.loan_account} onChange={(e) => update("loan_account", e.target.value)} placeholder="Use a demo or masked reference" /></label>
    </div>{error && <div className="form-error">{error}</div>}<div className="form-actions"><button type="button" className="secondary" onClick={() => void onClose()}>Cancel</button><button type="submit" disabled={submitting}>{submitting ? "Starting…" : "Start call"}</button></div></form>
  </section></div>;
}

function Detail({ call, onBack }: { call: Call; onBack: () => void }) {
  return <div className="detail-page">
    <button className="back" onClick={onBack}><ArrowLeft size={17} /> Back to calls</button>
    <div className="detail-hero">
      <div><div className="eyebrow">CALL RECORD · {call.call_id.slice(0, 8).toUpperCase()}</div><h1>{call.customer.name}</h1><p>{maskPhone(call.customer.phone)} · {call.customer.language === "es" ? "Spanish" : "English"} · {call.emi.loan_account}</p></div>
      <StagePill stage={call.stage_code} />
    </div>
    <div className="detail-grid">
      <section className="panel outcome-panel">
        <div className="panel-title"><div><span className="icon amber"><Sparkles size={18}/></span><h2>Call outcome</h2></div><span className="duration"><Clock3 size={14}/>{call.outcome?.duration_seconds || "—"} sec</span></div>
        <div className="outcome-copy">{call.outcome?.summary || "The call is still in progress. Analytics will appear after Gnani posts the result."}</div>
        <div className="facts">
          <div><span>Disposition</span><strong>{call.outcome?.disposition?.replaceAll("_", " ") || "Pending"}</strong></div>
          <div><span>Sentiment</span><strong className="capitalize">{call.outcome?.sentiment || "Unknown"}</strong></div>
          <div><span>EMI amount</span><strong>{money(call.emi.amount)}</strong></div>
          <div><span>Due date</span><strong>{new Date(call.emi.due_date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</strong></div>
        </div>
      </section>
      <section className="panel transcript-panel">
        <div className="panel-title"><div><span className="icon green"><Headphones size={18}/></span><h2>Conversation</h2></div><span className="language">{call.customer.language.toUpperCase()}</span></div>
        <div className="transcript">
          {call.transcript.length ? call.transcript.map((turn, i) => <div className={`turn ${turn.speaker}`} key={i}><div className="avatar">{turn.speaker === "agent" ? "AI" : call.customer.name[0]}</div><div><span>{turn.speaker === "agent" ? "Gnani agent" : call.customer.name}</span><p>{turn.text}</p></div></div>) : <div className="empty">No transcript has been received yet.</div>}
        </div>
      </section>
      <section className="panel payload-panel">
        <div className="panel-title"><div><span className="icon slate"><ShieldCheck size={18}/></span><h2>Provider payload</h2></div><span className="verified">Verified webhook</span></div>
        <pre>{JSON.stringify(call.raw_payload || { status: "awaiting_webhook", provider_call_id: call.provider_call_id }, null, 2)}</pre>
      </section>
    </div>
  </div>;
}

function Dashboard() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loadError, setLoadError] = useState("");
  const [demoMode, setDemoMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [stage, setStage] = useState("all");
  const [selected, setSelected] = useState<Call | null>(null);
  const [view, setView] = useState<"overview" | "calls" | "schedules">("overview");
  const [newCallOpen, setNewCallOpen] = useState(false);

  const refreshDashboard = async () => {
    try {
      const data = await getDashboard();
      setCalls(data.calls); setSummary(data.summary); setDemoMode(data.demo); setLoadError("");
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "The backend could not be reached.");
    } finally { setLoading(false); }
  };
  useEffect(() => { void refreshDashboard(); }, []);

  const filtered = useMemo(() => calls.filter((call) => {
    const text = `${call.customer.name} ${call.customer.customer_id} ${call.emi.loan_account}`.toLowerCase();
    return (stage === "all" || call.stage_code === stage) && text.includes(search.toLowerCase());
  }), [calls, search, stage]);
  const scheduled = useMemo(() => calls.filter((call) => ["promise_to_pay", "follow_up", "PTP_TODAY", "PTP_TOMORROW", "PTP_FUTURE", "PTP_PARTIAL", "CALLBACK_SCHEDULED"].includes(call.stage_code)), [calls]);

  if (selected) return <Detail call={selected} onBack={() => { setSelected(null); window.history.replaceState({}, "", "/"); }} />;

  const stats = [
    { label: "Calls placed", value: summary?.total_calls.toLocaleString() || "—", note: "This collection cycle", icon: PhoneCall, tone: "ink" },
    { label: "Promise to pay", value: (summary?.stages.promise_to_pay?.count || 0) + (summary?.stages.PTP_TODAY?.count || 0) + (summary?.stages.PTP_TOMORROW?.count || 0) + (summary?.stages.PTP_FUTURE?.count || 0) + (summary?.stages.PTP_PARTIAL?.count || 0), note: "Confirmed payment commitments", icon: Users, tone: "amber" },
    { label: "Payments confirmed", value: (summary?.stages.paid?.count || 0) + (summary?.stages.ALREADY_PAID?.count || 0), note: money((summary?.stages.paid?.amount || 0) + (summary?.stages.ALREADY_PAID?.amount || 0)), icon: CircleDollarSign, tone: "green" },
    { label: "Portfolio contacted", value: money(summary?.total_amount || 0), note: "Across active EMI calls", icon: TrendingUp, tone: "blue" },
  ];

  const showCalls = view === "calls";
  const showSchedules = view === "schedules";

  return <div className="shell">
    <aside><Logo /><nav><a className={view === "overview" ? "active" : ""} onClick={() => setView("overview")}><span className="nav-square"><TrendingUp size={17}/></span>Overview</a><a className={showCalls ? "active" : ""} onClick={() => setView("calls")}><span className="nav-square"><PhoneCall size={17}/></span>All calls</a><a className={showSchedules ? "active" : ""} onClick={() => setView("schedules")}><span className="nav-square"><CalendarDays size={17}/></span>Schedules</a></nav><div className="aside-bottom"><div className="agent-card"><span className="pulse"/><div><strong>Gnani agent</strong><small>Mock mode active</small></div></div><div className="profile"><div className="profile-avatar">VV</div><div><strong>Vaishnavi V</strong><small>Collections ops</small></div></div></div></aside>
    <main>
      <header><div><div className="eyebrow">{showSchedules ? "PAYMENT & CALLBACK SCHEDULES" : showCalls ? "ALL COLLECTION CALLS" : "COLLECTIONS OVERVIEW"}</div><h1>{showSchedules ? "Upcoming commitments" : showCalls ? "All calls" : "Good Morning Vaishnavi V"}</h1><p>{showSchedules ? "Track promised payments and requested callbacks." : showCalls ? "Search and review every collection conversation." : "Here’s how your EMI portfolio is moving today."}</p></div><div className="header-actions"><span className="date"><CalendarDays size={16}/>Jul 26, 2026</span><button onClick={() => setNewCallOpen(true)}><PhoneCall size={16}/>New call</button></div></header>
      {demoMode && <div className="demo-banner"><Sparkles size={16}/><span>Demo data</span> — sample records keep every view useful until the Atlas-backed API is connected.</div>}
      {loadError && <div className="demo-banner"><Sparkles size={16}/><span>Backend unavailable</span> — {loadError}</div>}
      {!showSchedules && !showCalls && <section className="stats">{stats.map(({ label, value, note, icon: Icon, tone }) => <div className="stat" key={label}><div className={`stat-icon ${tone}`}><Icon size={20}/></div><div className="stat-label">{label}</div><strong>{value}</strong><small>{note}</small></div>)}</section>}
      {showSchedules ? <section className="workspace"><div className="workspace-head"><div><h2>Schedules</h2><p>Follow up on customer commitments.</p></div></div><div className="table-wrap"><table><thead><tr><th>Customer</th><th>Commitment</th><th>Due date</th><th>Latest outcome</th><th/></tr></thead><tbody>{scheduled.map((call) => <tr key={call.call_id} onClick={() => setSelected(call)}><td><strong>{call.customer.name}</strong><span>{maskPhone(call.customer.phone)}</span></td><td><strong>{call.stage_code === "follow_up" ? "Callback requested" : "Promise to pay"}</strong><span>{call.outcome?.summary || "Awaiting confirmation"}</span></td><td><strong>{new Date(call.emi.due_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</strong></td><td><StagePill stage={call.stage_code}/></td><td><button className="row-go" aria-label={`Open ${call.customer.name}`}><ChevronRight size={18}/></button></td></tr>)}{!scheduled.length && <tr><td colSpan={5}><div className="empty">No callbacks or payment commitments are scheduled.</div></td></tr>}</tbody></table></div></section> : <section className="workspace">
        <div className="workspace-head"><div><h2>{showCalls ? "All calls" : "Recent calls"}</h2><p>{showCalls ? "Track every collection conversation." : "Track every conversation from dial to outcome."}</p></div>{!showCalls && <button className="text-button" onClick={() => setView("calls")}>View all <ArrowUpRight size={15}/></button>}</div>
        <div className="filters"><label><Search size={17}/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search customer or loan ID" /></label><div className="tabs">{["all", "promise_to_pay", "paid", "follow_up", "unreachable"].map((item) => <button onClick={() => setStage(item)} className={stage === item ? "active" : ""} key={item}>{item === "all" ? "All calls" : labels[item]}</button>)}</div></div>
        <div className="table-wrap"><table><thead><tr><th>Customer</th><th>EMI details</th><th>Call outcome</th><th>Last activity</th><th/></tr></thead><tbody>
          {loading ? <tr><td colSpan={5}><div className="empty">Loading call activity…</div></td></tr> : filtered.map((call) => <tr key={call.call_id} onClick={() => setSelected(call)}>
            <td><div className="customer"><div className="mini-avatar">{call.customer.name.split(" ").map(v => v[0]).join("").slice(0,2)}</div><div><strong>{call.customer.name}</strong><span>{maskPhone(call.customer.phone)} · {call.customer.language.toUpperCase()}</span></div></div></td>
            <td><strong>{money(call.emi.amount)}</strong><span>{call.emi.loan_account} · Due {new Date(call.emi.due_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span></td>
            <td><StagePill stage={call.stage_code}/></td><td><strong>{timeAgo(call.updated_at)}</strong><span>{call.outcome?.duration_seconds ? `${call.outcome.duration_seconds} sec call` : "Awaiting result"}</span></td><td><button className="row-go" aria-label={`Open ${call.customer.name}`}><ChevronRight size={18}/></button></td>
          </tr>)}
          {!loading && !filtered.length && <tr><td colSpan={5}><div className="empty">No calls match these filters.</div></td></tr>}
        </tbody></table></div>
        <div className="table-foot"><span>Showing {filtered.length} of {calls.length} recent calls</span><span>Data refreshed just now</span></div>
      </section>}
    </main>{newCallOpen && <NewCallDialog onClose={async () => setNewCallOpen(false)} onCreated={refreshDashboard} />}
  </div>;
}

export function App() { return <Dashboard />; }
