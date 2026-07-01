from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .config import (
    OAuthRequiredError,
    build_oauth_flow,
    get_google_scopes,
    get_settings,
    persist_token,
)
from .gmail_api import build_gmail_service, create_draft_reply, get_message, list_unread_messages, mark_as_read
from .gmail_api import build_gmail_thread_url, list_inbox_summaries, send_reply
from .logic import analyze_message, decide_next_action, generate_reply, get_gemini_client
from .manager_store import get_item as get_manager_item
from .manager_store import dashboard as manager_dashboard
from .manager_store import init_db, list_items as list_manager_items
from .manager_store import overview as manager_overview
from .manager_store import update_item as update_manager_item
from .manager_store import upsert_item
from .manager_ui import render_manager_app, render_privacy_policy, render_terms_of_service
from .sheets_api import build_sheets_service, find_customer_by_email


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
LOGGER = logging.getLogger(__name__)

app = FastAPI(title="ONEF Customer Success AI")
init_db()


NEWSLETTER_MARKERS = {
    "newsletter",
    "unsubscribe",
    "linkedin",
    "zoom",
    "notification",
    "digest",
    "invitation",
    "alerte de sécurité",
    "shared with you",
    "welcome to",
    "a récemment publié",
    "réagi à un post",
    "demande de connexion",
    "souhaite rejoindre votre réseau",
    "follow",
    "premium",
}
CUSTOMER_SCOPE_MARKERS = {
    "plainte",
    "remboursement",
    "commande",
    "livraison",
    "retard",
    "retour",
    "colis",
    "facture",
    "problème",
    "problem",
}
SIMPLE_REQUEST_INTENTS = {"question", "demande_info", "suivi_commande"}
VIP_TOTAL_THRESHOLD = 100000
VIP_ORDER_THRESHOLD = 5
IGNORED_SENDER_DOMAINS = {"linkedin.com", "zoom.us"}


class ManagerUpdatePayload(BaseModel):
    status: str
    manager_notes: str | None = None


class DraftPayload(BaseModel):
    manager_notes: str | None = None


class SyncPayload(BaseModel):
    message_ids: list[str] | None = None
    limit: int | None = None


class SendPayload(BaseModel):
    manager_notes: str | None = None


def process_inbox(limit: int | None = None) -> dict[str, Any]:
    settings = get_settings()
    gmail_service = build_gmail_service()
    sheets_service = build_sheets_service() if settings.spreadsheet_id else None
    llm_client = get_gemini_client(settings.gemini_api_key)

    messages = list_unread_messages(gmail_service, max_results=limit or settings.max_messages_per_run)
    processed: list[dict[str, Any]] = []

    for message_ref in messages:
        try:
            message = get_message(gmail_service, message_ref["id"])
            customer_record = None
            if sheets_service and settings.spreadsheet_id and message.sender_email:
                try:
                    customer_record = find_customer_by_email(
                        sheets_service,
                        settings.spreadsheet_id,
                        settings.spreadsheet_range,
                        message.sender_email,
                    )
                except Exception:
                    LOGGER.exception(
                        "Customer lookup failed for %s; continuing without spreadsheet context",
                        message.sender_email,
                    )

            analysis = analyze_message(
                llm_client,
                settings.gemini_model,
                message.body or message.snippet,
                customer_record,
            )
            decision = decide_next_action(
                analysis,
                customer_record,
                auto_send_enabled=settings.auto_send_replies,
                allow_auto_send_furious=settings.allow_auto_send_furious,
            )

            sender_name = parseaddr(message.sender)[0] or (customer_record or {}).get("nom") or "client"
            reply = generate_reply(
                llm_client,
                settings.gemini_model,
                settings.company_name,
                settings.company_signature,
                settings.knowledge_base,
                sender_name,
                message.body or message.snippet,
                analysis,
                decision,
                customer_record,
            )
            if decision.auto_send_allowed:
                delivery_mode = "sent"
                delivery_result = send_reply(gmail_service, message, reply)
            else:
                delivery_mode = "draft"
                delivery_result = create_draft_reply(gmail_service, message, reply)
            mark_as_read(gmail_service, message.message_id)
            processed.append(
                {
                    "message_id": message.message_id,
                    "thread_id": message.thread_id,
                    "from": message.sender_email,
                    "subject": message.subject,
                    "sentiment": analysis.sentiment,
                    "urgency": analysis.urgency,
                    "intent": analysis.intent,
                    "action": decision.action_label,
                    "discount_pct": decision.discount_pct,
                    "delivery_mode": delivery_mode,
                    "delivery_id": delivery_result["id"],
                    "auto_send_allowed": decision.auto_send_allowed,
                    "escalation_reason": decision.escalation_reason,
                }
            )
        except Exception as exc:
            LOGGER.exception("Message processing failed for %s", message_ref["id"])
            processed.append({"message_id": message_ref["id"], "error": str(exc)})

    return {
        "processed_count": len(processed),
        "messages": processed,
    }


def sync_manager_inbox(limit: int | None = None, message_ids: list[str] | None = None) -> dict[str, Any]:
    settings = get_settings()
    gmail_service = build_gmail_service()
    sheets_service = build_sheets_service() if settings.spreadsheet_id else None
    llm_client = get_gemini_client(settings.gemini_api_key)
    synced = 0

    if message_ids:
        refs = [{"id": message_id} for message_id in message_ids]
    else:
        refs = list_unread_messages(gmail_service, max_results=limit or settings.max_messages_per_run)

    for message_ref in refs:
        queue_item = build_manager_entry(
            gmail_service,
            sheets_service,
            llm_client,
            settings,
            message_ref["id"],
        )
        upsert_item(queue_item)
        synced += 1
        if queue_item["delivery_mode"] == "sent":
            mark_as_read(gmail_service, message_ref["id"])

    return {"synced_count": synced, "overview": manager_overview(), "dashboard": manager_dashboard()}


def build_manager_entry(
    gmail_service: Any,
    sheets_service: Any,
    llm_client: str | None,
    settings: Any,
    message_id: str,
) -> dict[str, Any]:
    message = get_message(gmail_service, message_id)
    customer_record = None
    if sheets_service and settings.spreadsheet_id and message.sender_email:
        try:
            customer_record = find_customer_by_email(
                sheets_service,
                settings.spreadsheet_id,
                settings.spreadsheet_range,
                message.sender_email,
            )
        except Exception:
            LOGGER.exception("Customer lookup failed for manager sync: %s", message.sender_email)

    analysis = analyze_message(
        llm_client,
        settings.gemini_model,
        message.body or message.snippet,
        customer_record,
    )
    decision = decide_next_action(
        analysis,
        customer_record,
        auto_send_enabled=True,
        allow_auto_send_furious=False,
    )
    relevance, ignore_reason = classify_scope(message, analysis)
    sender_name = parseaddr(message.sender)[0] or (customer_record or {}).get("nom") or "client"
    reply_text = ""
    if relevance != "irrelevant":
        reply_text = generate_reply(
            llm_client,
            settings.gemini_model,
            settings.company_name,
            settings.company_signature,
            settings.knowledge_base,
            sender_name,
            message.body or message.snippet,
            analysis,
            decision,
            customer_record,
        )
    queue_item = build_manager_queue_item(
        message,
        customer_record,
        analysis,
        decision,
        reply_text,
        relevance=relevance,
        ignore_reason=ignore_reason,
    )
    if should_auto_send(queue_item):
        delivery_result = send_reply(gmail_service, message, reply_text)
        queue_item["delivery_mode"] = "sent"
        queue_item["delivery_id"] = delivery_result["id"]
        queue_item["status"] = "sent"
        queue_item["processed_at"] = utc_now()
    return queue_item


def build_manager_queue_item(
    message: Any,
    customer_record: dict[str, Any] | None,
    analysis: Any,
    decision: Any,
    reply_text: str,
    *,
    relevance: str | None = None,
    ignore_reason: str | None = None,
) -> dict[str, Any]:
    customer_record = customer_record or {}
    relevance = relevance or classify_scope(message, analysis)[0]
    total_achats = float(customer_record.get("total_achats", 0) or 0)
    nombre_commandes = int(customer_record.get("nombre_commandes", 0) or 0)
    is_vip = total_achats >= VIP_TOTAL_THRESHOLD or nombre_commandes >= VIP_ORDER_THRESHOLD
    simple_request = analysis.intent in SIMPLE_REQUEST_INTENTS and analysis.sentiment in {"CALME", "NEUTRE"}
    needs_human_validation = (
        analysis.sentiment == "FURIEUX"
        or is_vip
        or analysis.intent == "remboursement"
        or total_achats >= VIP_TOTAL_THRESHOLD
    )
    status = "ignored" if relevance == "irrelevant" else "new"
    priority = derive_priority(analysis, is_vip)
    complaint_category = classify_complaint_category(message, analysis)
    return {
        "message_id": message.message_id,
        "thread_id": message.thread_id,
        "sender": message.sender,
        "sender_email": message.sender_email,
        "subject": message.subject,
        "snippet": message.snippet,
        "body": message.body,
        "status": status,
        "priority": priority,
        "relevance": relevance,
        "ignore_reason": ignore_reason,
        "sentiment": analysis.sentiment,
        "urgency": analysis.urgency,
        "intent": analysis.intent,
        "risk_level": analysis.risk_level,
        "confidence": analysis.confidence,
        "action_label": decision.action_label,
        "escalation_reason": decision.escalation_reason,
        "customer_name": customer_record.get("nom") or parseaddr(message.sender)[0],
        "customer_email": customer_record.get("email") or message.sender_email,
        "customer_json": customer_record,
        "total_achats": total_achats,
        "nombre_commandes": nombre_commandes,
        "is_vip": is_vip,
        "simple_request": simple_request,
        "needs_human_validation": needs_human_validation,
        "reply_text": reply_text if relevance != "irrelevant" else "",
        "delivery_mode": "pending",
        "delivery_id": None,
        "gmail_url": build_gmail_thread_url(message.thread_id),
        "complaint_category": complaint_category,
    }


def classify_scope(message: Any, analysis: Any) -> tuple[str, str | None]:
    sender_email = (message.sender_email or "").lower()
    sender_domain = sender_email.split("@")[-1] if "@" in sender_email else ""
    text = f"{message.subject} {message.snippet} {message.body}".lower()
    if is_internal_message(sender_email):
        return "irrelevant", "Message interne"
    if sender_domain in IGNORED_SENDER_DOMAINS:
        return "irrelevant", "Notification externe"
    if any(marker in sender_email for marker in {"noreply", "no-reply"}):
        return "irrelevant", "Expéditeur système"
    if any(marker in text for marker in NEWSLETTER_MARKERS):
        return "irrelevant", "Newsletter ou notification"
    if analysis.intent in {"plainte", "remboursement", "suivi_commande"}:
        return "relevant", None
    if any(marker in text for marker in CUSTOMER_SCOPE_MARKERS):
        return "relevant", None
    return "review", "À qualifier manuellement"


def is_internal_message(sender_email: str) -> bool:
    settings = get_settings()
    support_email = (settings.support_email or "").lower()
    if not sender_email or not support_email or "@" not in support_email:
        return False
    return sender_email.split("@")[-1] == support_email.split("@")[-1]


def derive_priority(analysis: Any, is_vip: bool) -> str:
    if analysis.sentiment == "FURIEUX" or analysis.intent == "remboursement" or is_vip:
        return "critical"
    if analysis.urgency == "HAUTE" or analysis.intent == "suivi_commande":
        return "high"
    return "normal"


def should_auto_send(item: dict[str, Any]) -> bool:
    return (
        item["relevance"] == "relevant"
        and item["simple_request"]
        and item["sentiment"] in {"CALME", "NEUTRE"}
        and float(item["confidence"] or 0) >= 0.75
        and not item["needs_human_validation"]
        and bool(item["reply_text"])
    )


def classify_complaint_category(message: Any, analysis: Any) -> str:
    text = f"{message.subject} {message.snippet} {message.body}".lower()
    if analysis.intent == "remboursement" or "remboursement" in text:
        return "Remboursement"
    if "commande" in text or "colis" in text or "livraison" in text:
        return "Commande"
    if analysis.intent == "plainte":
        return "Plainte"
    if analysis.intent == "suivi_commande":
        return "Suivi commande"
    if analysis.intent == "question":
        return "Question"
    return "Autre"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "ONEF Customer Success AI"}


@app.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "spreadsheet_configured": bool(settings.spreadsheet_id),
        "gemini_configured": bool(settings.gemini_api_key),
        "auto_send_replies": settings.auto_send_replies,
    }


@app.get("/manager", response_class=HTMLResponse)
def manager_console() -> str:
    return render_manager_app()


@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy() -> str:
    return render_privacy_policy()


@app.get("/terms", response_class=HTMLResponse)
def terms_of_service() -> str:
    return render_terms_of_service()


@app.get("/manager/api/items")
def manager_items() -> dict[str, Any]:
    return {"items": list_manager_items(), "overview": manager_overview(), "dashboard": manager_dashboard()}


@app.get("/manager/api/inbox")
def manager_inbox() -> dict[str, Any]:
    try:
        gmail_service = build_gmail_service()
        entries = []
        for summary in list_inbox_summaries(gmail_service, max_results=30):
            entries.append(
                {
                    "message_id": summary.message_id,
                    "thread_id": summary.thread_id,
                    "subject": summary.subject,
                    "sender": summary.sender,
                    "sender_email": summary.sender_email,
                    "snippet": summary.snippet,
                    "is_unread": summary.is_unread,
                    "gmail_url": build_gmail_thread_url(summary.thread_id),
                }
            )
        return {"items": entries}
    except OAuthRequiredError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post("/manager/api/sync")
def manager_sync(payload: SyncPayload | None = None) -> dict[str, Any]:
    try:
        payload = payload or SyncPayload()
        return sync_manager_inbox(limit=payload.limit, message_ids=payload.message_ids)
    except OAuthRequiredError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.patch("/manager/api/items/{message_id}")
def manager_update_item(message_id: str, payload: ManagerUpdatePayload) -> dict[str, Any]:
    item = get_manager_item(message_id)
    if not item:
        raise HTTPException(status_code=404, detail="Manager item not found")
    updated = update_manager_item(
        message_id,
        status=payload.status,
        manager_notes=payload.manager_notes,
        processed_at=utc_now() if payload.status == "treated" else item.get("processed_at"),
    )
    return {"item": updated}


@app.post("/manager/api/items/{message_id}/draft")
def manager_create_draft(message_id: str, payload: DraftPayload) -> dict[str, Any]:
    item = get_manager_item(message_id)
    if not item:
        raise HTTPException(status_code=404, detail="Manager item not found")
    if item.get("relevance") == "irrelevant":
        raise HTTPException(status_code=400, detail="Ignored items cannot generate drafts")
    if item.get("gmail_draft_id"):
        return {"item": item, "message": "Draft already exists"}

    gmail_service = build_gmail_service()
    message = get_message(gmail_service, message_id)
    draft = create_draft_reply(gmail_service, message, item.get("reply_text") or "")
    mark_as_read(gmail_service, message_id)
    updated = update_manager_item(
        message_id,
        gmail_draft_id=draft["id"],
        status="treated",
        delivery_mode="draft",
        delivery_id=draft["id"],
        manager_notes=payload.manager_notes,
        processed_at=utc_now(),
    )
    return {"item": updated, "draft_id": draft["id"]}


@app.post("/manager/api/items/{message_id}/send")
def manager_send_item(message_id: str, payload: SendPayload) -> dict[str, Any]:
    item = get_manager_item(message_id)
    if not item:
        raise HTTPException(status_code=404, detail="Manager item not found")
    if item.get("relevance") == "irrelevant":
        raise HTTPException(status_code=400, detail="Ignored items cannot be sent")
    if not item.get("reply_text"):
        raise HTTPException(status_code=400, detail="No reply available to send")
    if item.get("delivery_mode") == "sent":
        return {"item": item, "message": "Message already sent"}

    gmail_service = build_gmail_service()
    message = get_message(gmail_service, message_id)
    sent = send_reply(gmail_service, message, item.get("reply_text") or "")
    mark_as_read(gmail_service, message_id)
    updated = update_manager_item(
        message_id,
        delivery_mode="sent",
        delivery_id=sent["id"],
        status="sent",
        manager_notes=payload.manager_notes,
        processed_at=utc_now(),
    )
    return {"item": updated, "sent_id": sent["id"]}


@app.post("/run")
def run_now() -> dict[str, Any]:
    try:
        return process_inbox()
    except OAuthRequiredError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.get("/cron")
def run_cron(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    settings = get_settings()
    if settings.cron_secret:
        expected = f"Bearer {settings.cron_secret}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Invalid cron secret")
    return run_now()


@app.get("/google/oauth/start")
def oauth_start() -> dict[str, str]:
    flow = build_oauth_flow(scopes=get_google_scopes())
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account consent",
    )
    return {"authorization_url": authorization_url, "state": state}


@app.get("/google/oauth/callback")
def oauth_callback(request: Request) -> dict[str, Any]:
    state = request.query_params.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Missing state")

    flow = build_oauth_flow(scopes=get_google_scopes(), state=state)
    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {exc}") from exc

    persist_token(flow.credentials)
    return {
        "message": "OAuth completed. Save this token in GOOGLE_TOKEN_JSON on Vercel if needed.",
        "token_json": json.loads(flow.credentials.to_json()),
    }


if __name__ == "__main__":
    result = process_inbox()
    print(json.dumps(result, indent=2, ensure_ascii=False))
