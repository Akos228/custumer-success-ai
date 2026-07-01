import base64
import logging
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import parseaddr
from typing import Any

from googleapiclient.discovery import build

from .config import load_google_credentials


LOGGER = logging.getLogger(__name__)


@dataclass
class GmailMessage:
    message_id: str
    thread_id: str
    gmail_message_id: str
    subject: str
    sender: str
    sender_email: str
    snippet: str
    body: str


@dataclass
class GmailMessageSummary:
    message_id: str
    thread_id: str
    subject: str
    sender: str
    sender_email: str
    snippet: str
    is_unread: bool


def build_gmail_service():
    credentials = load_google_credentials()
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def list_unread_messages(service: Any, max_results: int = 10) -> list[dict[str, str]]:
    return list_messages(service, label_ids=["INBOX", "UNREAD"], max_results=max_results)


def list_messages(
    service: Any,
    *,
    label_ids: list[str] | None = None,
    max_results: int = 10,
    q: str | None = None,
) -> list[dict[str, str]]:
    response = (
        service.users()
        .messages()
        .list(userId="me", labelIds=label_ids, maxResults=max_results, q=q)
        .execute()
    )
    return response.get("messages", [])


def list_inbox_summaries(service: Any, max_results: int = 25) -> list[GmailMessageSummary]:
    summaries: list[GmailMessageSummary] = []
    for message_ref in list_messages(service, label_ids=["INBOX"], max_results=max_results):
        response = (
            service.users()
            .messages()
            .get(userId="me", id=message_ref["id"], format="metadata", metadataHeaders=["From", "Subject"])
            .execute()
        )
        headers = {header["name"].lower(): header["value"] for header in response["payload"].get("headers", [])}
        sender = headers.get("from", "")
        _, sender_email = parseaddr(sender)
        summaries.append(
            GmailMessageSummary(
                message_id=response["id"],
                thread_id=response["threadId"],
                subject=headers.get("subject", "(Sans objet)"),
                sender=sender,
                sender_email=sender_email.lower(),
                snippet=response.get("snippet", ""),
                is_unread="UNREAD" in response.get("labelIds", []),
            )
        )
    return summaries


def get_message(service: Any, message_id: str) -> GmailMessage:
    response = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    headers = {header["name"].lower(): header["value"] for header in response["payload"].get("headers", [])}
    sender = headers.get("from", "")
    _, sender_email = parseaddr(sender)
    return GmailMessage(
        message_id=response["id"],
        thread_id=response["threadId"],
        gmail_message_id=headers.get("message-id", ""),
        subject=headers.get("subject", "(Sans objet)"),
        sender=sender,
        sender_email=sender_email.lower(),
        snippet=response.get("snippet", ""),
        body=_extract_body(response.get("payload", {})).strip(),
    )


def create_draft_reply(service: Any, message: GmailMessage, reply_body: str) -> dict[str, Any]:
    encoded_message = _build_raw_reply(message, reply_body)
    draft = (
        service.users()
        .drafts()
        .create(
            userId="me",
            body={"message": {"raw": encoded_message, "threadId": message.thread_id}},
        )
        .execute()
    )
    LOGGER.info("Draft created for %s", message.sender_email)
    return draft


def send_reply(service: Any, message: GmailMessage, reply_body: str) -> dict[str, Any]:
    encoded_message = _build_raw_reply(message, reply_body)
    sent = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encoded_message, "threadId": message.thread_id})
        .execute()
    )
    LOGGER.info("Reply sent to %s", message.sender_email)
    return sent


def _build_raw_reply(message: GmailMessage, reply_body: str) -> str:
    email = EmailMessage()
    email["To"] = message.sender_email or message.sender
    email["Subject"] = _reply_subject(message.subject)
    if message.gmail_message_id:
        email["In-Reply-To"] = message.gmail_message_id
        email["References"] = message.gmail_message_id
    email.set_content(reply_body)
    return base64.urlsafe_b64encode(email.as_bytes()).decode("utf-8")


def mark_as_read(service: Any, message_id: str) -> None:
    (
        service.users()
        .messages()
        .modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]})
        .execute()
    )


def _reply_subject(subject: str) -> str:
    return subject if subject.lower().startswith("re:") else f"Re: {subject}"


def build_gmail_thread_url(thread_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"


def _extract_body(payload: dict[str, Any]) -> str:
    body = payload.get("body", {})
    data = body.get("data")
    if data:
        return _decode_base64(data)

    parts = payload.get("parts", [])
    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return _decode_base64(part["body"]["data"])

    for part in parts:
        nested = _extract_body(part)
        if nested:
            return nested

    return ""


def _decode_base64(value: str) -> str:
    padded = value + "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="ignore")
    except Exception:
        LOGGER.exception("Unable to decode message body")
        return ""
