import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOKEN_PATH = PROJECT_ROOT / "token.json"
DEFAULT_CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
LEGACY_CREDENTIALS_PATH = PROJECT_ROOT / "src" / "credentials.json"
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


class OAuthRequiredError(RuntimeError):
    pass


@dataclass(frozen=True)
class AppConfig:
    gemini_api_key: str | None
    gemini_model: str
    company_name: str
    company_signature: str
    support_email: str | None
    auto_send_replies: bool
    allow_auto_send_furious: bool
    knowledge_base: str | None
    spreadsheet_id: str | None
    spreadsheet_range: str
    max_messages_per_run: int
    token_file: Path
    oauth_callback_path: str
    app_base_url: str | None
    cron_secret: str | None

    @property
    def oauth_redirect_uri(self) -> str:
        if os.getenv("GOOGLE_REDIRECT_URI"):
            return os.environ["GOOGLE_REDIRECT_URI"]
        web_config = load_google_client_config().get("web", {})
        redirect_uris = web_config.get("redirect_uris") or []
        if redirect_uris:
            return redirect_uris[0]
        if self.app_base_url:
            return f"{self.app_base_url.rstrip('/')}/{self.oauth_callback_path.lstrip('/')}"
        return f"http://localhost:8000/{self.oauth_callback_path.lstrip('/')}"


def get_settings() -> AppConfig:
    token_file = Path(os.getenv("GOOGLE_TOKEN_FILE", DEFAULT_TOKEN_PATH))
    callback_path = os.getenv("GOOGLE_OAUTH_CALLBACK_PATH", "/google/oauth/callback")
    return AppConfig(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        company_name=os.getenv("COMPANY_NAME", "ONEF"),
        company_signature=os.getenv("COMPANY_SIGNATURE", "L'equipe ONEF"),
        support_email=os.getenv("SUPPORT_EMAIL"),
        auto_send_replies=os.getenv("AUTO_SEND_REPLIES", "false").lower() == "true",
        allow_auto_send_furious=os.getenv("ALLOW_AUTO_SEND_FURIOUS", "false").lower() == "true",
        knowledge_base=os.getenv("KNOWLEDGE_BASE_TEXT"),
        spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"),
        spreadsheet_range=os.getenv("GOOGLE_SHEETS_RANGE", "Clients!A:Z"),
        max_messages_per_run=int(os.getenv("MAX_MESSAGES_PER_RUN", "10")),
        token_file=token_file,
        oauth_callback_path=callback_path,
        app_base_url=os.getenv("APP_BASE_URL"),
        cron_secret=os.getenv("CRON_SECRET"),
    )


def get_google_scopes() -> list[str]:
    scopes = os.getenv("GOOGLE_SCOPES")
    if not scopes:
        return DEFAULT_SCOPES.copy()
    return [scope.strip() for scope in scopes.split(",") if scope.strip()]


def load_google_client_config() -> dict[str, Any]:
    raw_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if raw_json:
        return json.loads(raw_json)

    credentials_file = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", DEFAULT_CREDENTIALS_PATH))
    if credentials_file.exists():
        return json.loads(credentials_file.read_text(encoding="utf-8"))
    if not os.getenv("GOOGLE_CREDENTIALS_FILE") and LEGACY_CREDENTIALS_PATH.exists():
        return json.loads(LEGACY_CREDENTIALS_PATH.read_text(encoding="utf-8"))

    raise FileNotFoundError(
        "Google OAuth credentials are missing. Set GOOGLE_CREDENTIALS_JSON or provide credentials.json."
    )


def build_oauth_flow(
    *,
    scopes: list[str] | None = None,
    state: str | None = None,
    redirect_uri: str | None = None,
) -> Flow:
    flow = Flow.from_client_config(
        load_google_client_config(),
        scopes=scopes or get_google_scopes(),
        state=state,
    )
    flow.redirect_uri = redirect_uri or get_settings().oauth_redirect_uri
    return flow


def load_google_credentials(scopes: list[str] | None = None) -> Credentials:
    scopes = scopes or get_google_scopes()
    token_json = os.getenv("GOOGLE_TOKEN_JSON")

    credentials: Credentials | None = None
    if token_json:
        credentials = Credentials.from_authorized_user_info(json.loads(token_json), scopes=scopes)
    else:
        settings = get_settings()
        if settings.token_file.exists():
            credentials = Credentials.from_authorized_user_file(str(settings.token_file), scopes=scopes)

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            persist_token(credentials)
        except RefreshError as exc:
            raise OAuthRequiredError(
                "Google token expired or revoked. Start OAuth with /google/oauth/start locally "
                "or /api/google/oauth/start on Vercel, then update GOOGLE_TOKEN_JSON."
            ) from exc

    if not credentials or not credentials.valid:
        raise OAuthRequiredError(
            "Google token missing or invalid. Start OAuth with /google/oauth/start locally "
            "or /api/google/oauth/start on Vercel, or set GOOGLE_TOKEN_JSON."
        )

    return credentials


def persist_token(credentials: Credentials) -> None:
    token_payload = credentials.to_json()
    token_path = get_settings().token_file
    try:
        token_path.write_text(token_payload, encoding="utf-8")
    except OSError:
        # Vercel's filesystem is ephemeral; returning the token in the callback remains the fallback.
        pass


def build_public_url(path: str) -> str:
    settings = get_settings()
    if settings.app_base_url:
        return f"{settings.app_base_url.rstrip('/')}/{path.lstrip('/')}"
    return path
