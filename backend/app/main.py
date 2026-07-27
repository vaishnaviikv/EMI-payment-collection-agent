import hashlib
import hmac
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal

from bson.decimal128 import Decimal128
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from .config import Settings, get_settings
from .gnani import GnaniClient, GnaniError
from .logging import configure_logging
from .models import CallCreated, CallView, InitialMessageRequest, PostCallWebhook
from .repository import CallRepository, utcnow

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def jsonable(value):
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items() if k != "_id"}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    return value


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "repo"):
        client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
        app.state.mongo_client = client
        app.state.repo = CallRepository(client[settings.mongodb_database])
        await app.state.repo.ensure_indexes()
    app.state.gnani = getattr(app.state, "gnani", GnaniClient(settings))
    yield
    if hasattr(app.state, "mongo_client"):
        app.state.mongo_client.close()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Webhook-API-Key", "X-Webhook-Id"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("unhandled_request_error", extra={"request_id": request_id, "path": request.url.path})
        raise
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": exc.errors()}},
    )


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


def repo(request: Request):
    return request.app.state.repo


def gnani(request: Request):
    return request.app.state.gnani


@app.get("/health/live")
async def live():
    return {"status": "ok"}


@app.get("/health/ready")
async def ready(repository=Depends(repo)):
    try:
        await repository.collection.database.command("ping")
    except Exception as exc:
        raise HTTPException(503, {"code": "DATABASE_UNAVAILABLE", "message": "Database is unavailable"}) from exc
    return {"status": "ready"}


async def initiate_call(
    payload: InitialMessageRequest,
    repository: CallRepository,
    client: GnaniClient,
) -> CallCreated:
    call_id = str(uuid.uuid4())
    now = utcnow()
    document = {
        "call_id": call_id,
        "customer": {
            "customer_id": payload.customer_id,
            "name": payload.customer_name,
            "phone": payload.phone,
            "language": payload.language.value,
        },
        "emi": {
            "amount": Decimal128(payload.emi_amount),
            "currency": payload.currency,
            "due_date": payload.due_date.isoformat(),
            "loan_account": payload.loan_account,
        },
        "status": "pending",
        "stage_code": "pending_call",
        "webhook_ids": [],
        "transcript": [],
        "outcome": None,
        "raw_payload": None,
        "created_at": now,
        "updated_at": now,
    }
    await repository.create(document)
    try:
        result = await client.trigger(call_id, payload.model_dump(mode="json"))
        await repository.update_trigger(call_id, result.provider_call_id)
        return CallCreated(
            call_id=call_id,
            status="triggered",
            provider_call_id=result.provider_call_id,
            message="Call queued in mock mode" if result.mocked else "Call queued with Gnani",
        )
    except GnaniError as exc:
        await repository.mark_trigger_failed(call_id, str(exc))
        logger.warning("gnani_trigger_failed", extra={"call_id": call_id})
        raise HTTPException(
            502,
            {"code": "CALL_TRIGGER_FAILED", "message": "Call was saved, but the provider trigger failed", "call_id": call_id},
        ) from exc


@app.post("/api/Initial_Message", response_model=CallCreated, status_code=201)
async def initial_message(
    payload: InitialMessageRequest,
    repository=Depends(repo),
    client: GnaniClient = Depends(gnani),
):
    return await initiate_call(payload, repository, client)


@app.post("/api/v1/webhooks/post-call")
async def post_call(
    payload: PostCallWebhook,
    request: Request,
    x_webhook_api_key: str | None = Header(default=None),
    x_webhook_id: str | None = Header(default=None),
    repository=Depends(repo),
):
    if not x_webhook_api_key or not hmac.compare_digest(x_webhook_api_key, settings.webhook_api_key):
        raise HTTPException(401, {"code": "INVALID_WEBHOOK_KEY", "message": "Webhook authentication failed"})
    raw = payload.model_dump(mode="json")
    delivery_id = x_webhook_id or hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()
    existing = await repository.get(payload.call_id)
    if not existing:
        raise HTTPException(404, {"code": "CALL_NOT_FOUND", "message": "No matching call record"})
    if delivery_id in existing.get("webhook_ids", []):
        return {"status": "duplicate", "call_id": payload.call_id}
    disposition = payload.DISPOSITION.strip().upper()
    # Gnani's DISPOSITION enum is the assignment's canonical stage code.
    # Legacy mappings remain supported, but never discard an allowed Gnani code.
    stage_code = settings.disposition_map.get(disposition, disposition)
    outcome = {**payload.analytics.model_dump(), "disposition": disposition}
    update = {
        "status": "completed",
        "stage_code": stage_code,
        "transcript": [turn.model_dump() for turn in payload.transcript],
        "outcome": outcome,
        "raw_payload": raw,
        "updated_at": utcnow(),
    }
    if payload.provider_call_id:
        update["provider_call_id"] = payload.provider_call_id
    updated = await repository.apply_webhook(payload.call_id, delivery_id, update)
    if not updated:
        return {"status": "duplicate", "call_id": payload.call_id}
    logger.info("post_call_applied", extra={"call_id": payload.call_id, "stage_code": stage_code})
    return {"status": "accepted", "call_id": payload.call_id, "stage_code": stage_code}


@app.get("/api/calls")
async def list_calls(
    request: Request,
    stage_code: str | None = None,
    status: str | None = None,
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repository=Depends(repo),
):
    rows, total = await repository.list(
        {"stage_code": stage_code, "status": status, "search": search}, limit, offset
    )
    return {"items": [jsonable(row) for row in rows], "total": total, "limit": limit, "offset": offset}


@app.get("/api/calls/{call_id}", response_model=CallView)
async def call_detail(call_id: str, repository=Depends(repo)):
    row = await repository.get(call_id)
    if not row:
        raise HTTPException(404, {"code": "CALL_NOT_FOUND", "message": "No matching call record"})
    return jsonable(row)


@app.get("/api/dashboard/summary")
async def dashboard_summary(repository=Depends(repo)):
    return jsonable(await repository.summary())
