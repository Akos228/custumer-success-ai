from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from .config import load_google_credentials


EMAIL_ALIASES = {"email", "mail", "email_client", "adresse_email"}
TOTAL_ALIASES = {
    "total_achats",
    "total achats",
    "total",
    "montant_total",
    "achats_total",
    "lifetime_value",
}
ORDER_COUNT_ALIASES = {"nombre_commandes", "nb_commandes", "orders", "commandes"}
NAME_ALIASES = {"nom", "name", "client", "customer_name"}


def build_sheets_service():
    credentials = load_google_credentials()
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def find_customer_by_email(service: Any, spreadsheet_id: str, sheet_range: str, email: str) -> dict[str, Any] | None:
    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=sheet_range)
        .execute()
    )
    rows = response.get("values", [])
    if len(rows) < 2:
        return None

    headers = [normalize_header(value) for value in rows[0]]
    for row in rows[1:]:
        record = row_to_record(headers, row)
        record_email = first_present(record, EMAIL_ALIASES)
        if record_email and record_email.lower() == email.lower():
            record["total_achats"] = parse_number(first_present(record, TOTAL_ALIASES))
            record["nombre_commandes"] = int(parse_number(first_present(record, ORDER_COUNT_ALIASES)))
            record["nom"] = first_present(record, NAME_ALIASES) or email
            return record
    return None


def row_to_record(headers: list[str], row: list[str]) -> dict[str, str]:
    record: dict[str, str] = {}
    for index, header in enumerate(headers):
        if not header:
            continue
        record[header] = row[index] if index < len(row) else ""
    return record


def normalize_header(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def first_present(record: dict[str, Any], candidates: set[str]) -> Any:
    for candidate in candidates:
        if candidate in record and record[candidate] not in ("", None):
            return record[candidate]
    return None


def parse_number(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    normalized = str(value).replace("FCFA", "").replace(" ", "").replace(",", ".")
    normalized = "".join(char for char in normalized if char.isdigit() or char in ".-")
    try:
        return float(normalized)
    except ValueError:
        return 0.0
