# Architecture and request flow

```mermaid
sequenceDiagram
  participant UI as React dashboard
  participant API as FastAPI
  participant DB as MongoDB Atlas
  participant GN as Gnani
  UI->>API: POST /api/Initial_Message
  API->>DB: insert pending call
  API->>GN: trigger with pre-call variables
  GN-->>API: provider call id
  API->>DB: mark triggered
  GN->>API: POST post-call + API key
  API->>DB: atomic dedupe and result update
  UI->>API: GET /api/calls
  API-->>UI: summaries and call records
```

The API is the only component allowed to reach Atlas or hold Gnani credentials. A call record is persisted before the external trigger, so provider outages remain observable. Webhook delivery IDs are added with an atomic conditional update, making retries safe.

