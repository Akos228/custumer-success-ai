from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "manager_queue.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db_path() -> Path:
    custom_path = os.getenv("MANAGER_DB_PATH")
    if custom_path:
        return Path(custom_path)
    if os.getenv("VERCEL") == "1":
        return Path("/tmp/manager_queue.db")
    return DEFAULT_DB_PATH


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(get_db_path())
    db.row_factory = sqlite3.Row
    return db


def init_db() -> None:
    with closing(connect()) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS manager_items (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                sender TEXT,
                sender_email TEXT,
                subject TEXT,
                snippet TEXT,
                body TEXT,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                relevance TEXT NOT NULL,
                ignore_reason TEXT,
                sentiment TEXT,
                urgency TEXT,
                intent TEXT,
                risk_level TEXT,
                confidence REAL,
                action_label TEXT,
                escalation_reason TEXT,
                customer_name TEXT,
                customer_email TEXT,
                customer_json TEXT,
                total_achats REAL DEFAULT 0,
                nombre_commandes INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                simple_request INTEGER DEFAULT 0,
                needs_human_validation INTEGER DEFAULT 0,
                reply_text TEXT,
                gmail_draft_id TEXT,
                delivery_mode TEXT DEFAULT 'pending',
                delivery_id TEXT,
                gmail_url TEXT,
                complaint_category TEXT,
                manager_notes TEXT,
                processed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_synced_at TEXT NOT NULL
            )
            """
        )
        _ensure_column(db, "manager_items", "delivery_mode", "TEXT DEFAULT 'pending'")
        _ensure_column(db, "manager_items", "delivery_id", "TEXT")
        _ensure_column(db, "manager_items", "gmail_url", "TEXT")
        _ensure_column(db, "manager_items", "complaint_category", "TEXT")
        db.commit()


def upsert_item(payload: dict[str, Any]) -> None:
    now = utc_now()
    data = {
        "message_id": payload["message_id"],
        "thread_id": payload["thread_id"],
        "sender": payload.get("sender"),
        "sender_email": payload.get("sender_email"),
        "subject": payload.get("subject"),
        "snippet": payload.get("snippet"),
        "body": payload.get("body"),
        "status": payload.get("status", "new"),
        "priority": payload.get("priority", "normal"),
        "relevance": payload.get("relevance", "review"),
        "ignore_reason": payload.get("ignore_reason"),
        "sentiment": payload.get("sentiment"),
        "urgency": payload.get("urgency"),
        "intent": payload.get("intent"),
        "risk_level": payload.get("risk_level"),
        "confidence": payload.get("confidence"),
        "action_label": payload.get("action_label"),
        "escalation_reason": payload.get("escalation_reason"),
        "customer_name": payload.get("customer_name"),
        "customer_email": payload.get("customer_email"),
        "customer_json": json.dumps(payload.get("customer_json") or {}, ensure_ascii=False),
        "total_achats": payload.get("total_achats", 0),
        "nombre_commandes": payload.get("nombre_commandes", 0),
        "is_vip": 1 if payload.get("is_vip") else 0,
        "simple_request": 1 if payload.get("simple_request") else 0,
        "needs_human_validation": 1 if payload.get("needs_human_validation") else 0,
        "reply_text": payload.get("reply_text"),
        "gmail_draft_id": payload.get("gmail_draft_id"),
        "delivery_mode": payload.get("delivery_mode", "pending"),
        "delivery_id": payload.get("delivery_id"),
        "gmail_url": payload.get("gmail_url"),
        "complaint_category": payload.get("complaint_category"),
        "manager_notes": payload.get("manager_notes"),
        "processed_at": payload.get("processed_at"),
        "updated_at": now,
        "last_synced_at": now,
    }
    with closing(connect()) as db:
        existing = db.execute(
            """
            SELECT created_at, gmail_draft_id, manager_notes, status, processed_at, delivery_mode, delivery_id
            FROM manager_items
            WHERE message_id = ?
            """,
            (data["message_id"],),
        ).fetchone()
        data["created_at"] = existing["created_at"] if existing else now
        if existing:
            if existing["gmail_draft_id"] and not data["gmail_draft_id"]:
                data["gmail_draft_id"] = existing["gmail_draft_id"]
            if existing["manager_notes"] and not data["manager_notes"]:
                data["manager_notes"] = existing["manager_notes"]
            if data["status"] == "new" and existing["status"] in {"in_progress", "treated", "ignored"}:
                data["status"] = existing["status"]
            if existing["processed_at"] and not data["processed_at"]:
                data["processed_at"] = existing["processed_at"]
            if existing["delivery_mode"] and data["delivery_mode"] == "pending":
                data["delivery_mode"] = existing["delivery_mode"]
            if existing["delivery_id"] and not data["delivery_id"]:
                data["delivery_id"] = existing["delivery_id"]
        db.execute(
            """
            INSERT INTO manager_items (
                message_id, thread_id, sender, sender_email, subject, snippet, body, status, priority, relevance,
                ignore_reason, sentiment, urgency, intent, risk_level, confidence, action_label, escalation_reason,
                customer_name, customer_email, customer_json, total_achats, nombre_commandes, is_vip, simple_request,
                needs_human_validation, reply_text, gmail_draft_id, delivery_mode, delivery_id, gmail_url,
                complaint_category, manager_notes, processed_at, created_at,
                updated_at, last_synced_at
            ) VALUES (
                :message_id, :thread_id, :sender, :sender_email, :subject, :snippet, :body, :status, :priority, :relevance,
                :ignore_reason, :sentiment, :urgency, :intent, :risk_level, :confidence, :action_label, :escalation_reason,
                :customer_name, :customer_email, :customer_json, :total_achats, :nombre_commandes, :is_vip, :simple_request,
                :needs_human_validation, :reply_text, :gmail_draft_id, :delivery_mode, :delivery_id, :gmail_url,
                :complaint_category, :manager_notes, :processed_at, :created_at,
                :updated_at, :last_synced_at
            )
            ON CONFLICT(message_id) DO UPDATE SET
                thread_id = excluded.thread_id,
                sender = excluded.sender,
                sender_email = excluded.sender_email,
                subject = excluded.subject,
                snippet = excluded.snippet,
                body = excluded.body,
                status = excluded.status,
                priority = excluded.priority,
                relevance = excluded.relevance,
                ignore_reason = excluded.ignore_reason,
                sentiment = excluded.sentiment,
                urgency = excluded.urgency,
                intent = excluded.intent,
                risk_level = excluded.risk_level,
                confidence = excluded.confidence,
                action_label = excluded.action_label,
                escalation_reason = excluded.escalation_reason,
                customer_name = excluded.customer_name,
                customer_email = excluded.customer_email,
                customer_json = excluded.customer_json,
                total_achats = excluded.total_achats,
                nombre_commandes = excluded.nombre_commandes,
                is_vip = excluded.is_vip,
                simple_request = excluded.simple_request,
                needs_human_validation = excluded.needs_human_validation,
                reply_text = excluded.reply_text,
                gmail_draft_id = excluded.gmail_draft_id,
                delivery_mode = excluded.delivery_mode,
                delivery_id = excluded.delivery_id,
                gmail_url = excluded.gmail_url,
                complaint_category = excluded.complaint_category,
                manager_notes = excluded.manager_notes,
                processed_at = excluded.processed_at,
                updated_at = excluded.updated_at,
                last_synced_at = excluded.last_synced_at
            """,
            data,
        )
        db.commit()


def list_items() -> list[dict[str, Any]]:
    with closing(connect()) as db:
        rows = db.execute(
            """
            SELECT *
            FROM manager_items
            ORDER BY
                CASE priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    ELSE 3
                END,
                updated_at DESC
            """
        ).fetchall()
    return [_row_to_item(row) for row in rows]


def get_item(message_id: str) -> dict[str, Any] | None:
    with closing(connect()) as db:
        row = db.execute("SELECT * FROM manager_items WHERE message_id = ?", (message_id,)).fetchone()
    return _row_to_item(row) if row else None


def update_item(message_id: str, **updates: Any) -> dict[str, Any] | None:
    if not updates:
        return get_item(message_id)
    updates["updated_at"] = utc_now()
    assignments = ", ".join(f"{key} = :{key}" for key in updates)
    updates["message_id"] = message_id
    with closing(connect()) as db:
        db.execute(f"UPDATE manager_items SET {assignments} WHERE message_id = :message_id", updates)
        db.commit()
    return get_item(message_id)


def overview() -> dict[str, Any]:
    items = list_items()
    counts = {
        "total": len(items),
        "new": 0,
        "in_progress": 0,
        "treated": 0,
        "ignored": 0,
        "sent": 0,
        "needs_validation": 0,
        "vip": 0,
        "auto_sent": 0,
        "clients": 0,
    }
    client_emails: set[str] = set()
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
        if item["needs_human_validation"]:
            counts["needs_validation"] += 1
        if item["is_vip"]:
            counts["vip"] += 1
        if item["delivery_mode"] == "sent":
            counts["auto_sent"] += 1
        if item.get("customer_email") and item["relevance"] != "irrelevant":
            client_emails.add(item["customer_email"])
    counts["clients"] = len(client_emails)
    return counts


def dashboard() -> dict[str, Any]:
    items = list_items()
    categories: dict[str, int] = {}
    complaints_by_day: dict[str, int] = {}
    clients: dict[str, dict[str, Any]] = {}
    for item in items:
        if item["relevance"] == "irrelevant":
            continue
        category = item.get("complaint_category") or "Autre"
        categories[category] = categories.get(category, 0) + 1
        created_day = (item.get("created_at") or "")[:10]
        if created_day:
            complaints_by_day[created_day] = complaints_by_day.get(created_day, 0) + 1
        email = item.get("customer_email") or item.get("sender_email") or "inconnu"
        entry = clients.setdefault(
            email,
            {
                "client": item.get("customer_name") or email,
                "email": email,
                "tickets": 0,
                "vip": False,
                "last_sentiment": item.get("sentiment"),
                "last_category": category,
            },
        )
        entry["tickets"] += 1
        entry["vip"] = entry["vip"] or item.get("is_vip", False)
        entry["last_sentiment"] = item.get("sentiment")
        entry["last_category"] = category

    client_rows = sorted(clients.values(), key=lambda row: (-row["tickets"], row["client"]))[:12]
    category_rows = [
        {"category": category, "count": count}
        for category, count in sorted(categories.items(), key=lambda pair: (-pair[1], pair[0]))
    ]
    timeline_rows = [
        {"date": date, "count": count}
        for date, count in sorted(complaints_by_day.items())
    ]
    return {
        "categories": category_rows,
        "timeline": timeline_rows,
        "clients": client_rows,
    }


def _row_to_item(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["customer_json"] = json.loads(item["customer_json"] or "{}")
    item["is_vip"] = bool(item["is_vip"])
    item["simple_request"] = bool(item["simple_request"])
    item["needs_human_validation"] = bool(item["needs_human_validation"])
    return item


def _ensure_column(db: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    rows = db.execute(f"PRAGMA table_info({table})").fetchall()
    if any(row[1] == column for row in rows):
        return
    db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
