# Architecture and request flow

```mermaid
sequenceDiagram
  participant Op as Operator
  participant GC as Gnani Agents Console
  participant API as FastAPI
  participant DB as MongoDB Atlas
  participant UI as React dashboard
  Op->>GC: start call (customer + EMI details)
  GC->>API: POST /api/Initial_Message
  API->>DB: insert call record (status=triggered)
  API-->>GC: dynamic initial_message
  GC->>Op: places outbound call, converses with customer
  GC->>API: POST /api/v1/webhooks/post-call + API key
  API->>DB: atomic dedupe and result update
  UI->>API: GET /api/calls
  API-->>UI: summaries and call records
```

The call itself is triggered manually inside the Gnani Agents Console, not by this API. The console calls `POST /api/Initial_Message` to fetch the dynamically generated greeting and to let the backend record the call as `triggered`; the API's endpoint must be publicly reachable for the console to call it. The API is the only component allowed to reach Atlas or hold the post-call webhook key. Webhook delivery IDs are added with an atomic conditional update, making retries safe. The dashboard is read-only — it never initiates or controls calls.

