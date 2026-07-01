from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import requests


LOGGER = logging.getLogger(__name__)

DEFAULT_MATRIX = [
    {
        "sentiment": "FURIEUX",
        "min_total_achats": 100000,
        "discount_pct": 20,
        "gesture_label": "remise de 20%",
    },
    {
        "sentiment": "FURIEUX",
        "min_total_achats": 50000,
        "discount_pct": 10,
        "gesture_label": "remise de 10%",
    },
    {
        "sentiment": "CALME",
        "min_total_achats": 100000,
        "discount_pct": 5,
        "gesture_label": "remise de 5%",
    },
]


@dataclass
class AnalysisResult:
    sentiment: str
    urgency: str
    needs_gesture: bool
    issue_summary: str
    customer_tone: str
    intent: str
    requested_action: str
    risk_level: str
    confidence: float


@dataclass
class DecisionResult:
    discount_pct: int
    gesture_label: str | None
    action_label: str
    rationale: str
    auto_send_allowed: bool
    escalation_reason: str | None


def get_gemini_client(api_key: str | None) -> str | None:
    return api_key or None


def analyze_message(
    client: str | None,
    model: str,
    email_body: str,
    customer_record: dict[str, Any] | None,
) -> AnalysisResult:
    if not client:
        return heuristic_analysis(email_body)

    customer_context = json.dumps(customer_record or {}, ensure_ascii=False)
    prompt = f"""
Analyse l'email client suivant et renvoie uniquement un JSON valide.

JSON attendu:
{{
  "sentiment": "FURIEUX|NEUTRE|CALME",
  "urgency": "HAUTE|MOYENNE|FAIBLE",
  "needs_gesture": true,
  "issue_summary": "resume en une phrase",
  "customer_tone": "description concise",
  "intent": "plainte|question|demande_info|suivi_commande|remboursement|remerciement|autre",
  "requested_action": "action attendue par le client",
  "risk_level": "FAIBLE|MOYEN|ELEVE",
  "confidence": 0.0
}}

Contexte client:
{customer_context}

Email:
\"\"\"{email_body}\"\"\"
""".strip()

    try:
        output = _invoke_text_model(client, model, prompt)
        payload = json.loads(_extract_json_object(output))
        return AnalysisResult(
            sentiment=payload.get("sentiment", "NEUTRE"),
            urgency=payload.get("urgency", "MOYENNE"),
            needs_gesture=bool(payload.get("needs_gesture", False)),
            issue_summary=payload.get("issue_summary", "Demande client à traiter."),
            customer_tone=payload.get("customer_tone", "professionnel"),
            intent=payload.get("intent", "autre"),
            requested_action=payload.get("requested_action", "Réponse à préciser."),
            risk_level=payload.get("risk_level", "MOYEN"),
            confidence=float(payload.get("confidence", 0.5) or 0.5),
        )
    except Exception:
        LOGGER.exception("Gemini analysis failed, using heuristic fallback")
        return heuristic_analysis(email_body)


def heuristic_analysis(email_body: str) -> AnalysisResult:
    lowered = email_body.lower()
    furious_markers = {"inadmissible", "scandale", "furieux", "colère", "honte", "déçu", "remboursement"}
    calm_markers = {"bonjour", "merci", "svp", "s'il vous plaît", "cordialement"}
    urgent_markers = {"urgent", "immédiat", "aujourd'hui", "rapidement", "asap"}
    sentiment = "NEUTRE"
    if any(marker in lowered for marker in furious_markers):
        sentiment = "FURIEUX"
    elif any(marker in lowered for marker in calm_markers):
        sentiment = "CALME"

    urgency = "HAUTE" if any(marker in lowered for marker in urgent_markers) else "MOYENNE"
    intent = "remboursement" if "remboursement" in lowered else "plainte" if sentiment == "FURIEUX" else "autre"
    needs_gesture = sentiment == "FURIEUX" or "geste commercial" in lowered
    risk_level = "ELEVE" if intent == "remboursement" or sentiment == "FURIEUX" else "MOYEN"
    return AnalysisResult(
        sentiment=sentiment,
        urgency=urgency,
        needs_gesture=needs_gesture,
        issue_summary=(email_body.strip() or "Message client reçu.")[:180],
        customer_tone="direct" if sentiment == "FURIEUX" else "courtois",
        intent=intent,
        requested_action="Traitement manuel recommandé." if risk_level == "ELEVE" else "Réponse simple",
        risk_level=risk_level,
        confidence=0.45,
    )


def decide_next_action(
    analysis: AnalysisResult,
    customer_record: dict[str, Any] | None,
    *,
    auto_send_enabled: bool,
    allow_auto_send_furious: bool,
) -> DecisionResult:
    customer_record = customer_record or {}
    total_achats = float(customer_record.get("total_achats", 0) or 0)
    matrix = load_decision_matrix()
    auto_send_allowed, escalation_reason = evaluate_auto_send_safety(
        analysis,
        auto_send_enabled=auto_send_enabled,
        allow_auto_send_furious=allow_auto_send_furious,
    )

    for rule in matrix:
        if rule["sentiment"] != analysis.sentiment:
            continue
        if total_achats < float(rule.get("min_total_achats", 0)):
            continue
        return DecisionResult(
            discount_pct=int(rule["discount_pct"]),
            gesture_label=rule.get("gesture_label"),
            action_label="GESTE_COMMERCIAL",
            rationale=f"Sentiment {analysis.sentiment} et total achats {int(total_achats)}.",
            auto_send_allowed=auto_send_allowed,
            escalation_reason=escalation_reason,
        )

    return DecisionResult(
        discount_pct=0,
        gesture_label=None,
        action_label="REPONSE_STANDARD",
        rationale=f"Aucune règle de geste commercial pour {analysis.sentiment}.",
        auto_send_allowed=auto_send_allowed,
        escalation_reason=escalation_reason,
    )


def generate_reply(
    client: str | None,
    model: str,
    company_name: str,
    company_signature: str,
    knowledge_base: str | None,
    sender_name: str,
    original_message: str,
    analysis: AnalysisResult,
    decision: DecisionResult,
    customer_record: dict[str, Any] | None,
) -> str:
    customer_record = customer_record or {}
    if not client:
        return build_fallback_reply(sender_name, analysis, decision, company_signature)

    gesture_sentence = (
        f"Propose explicitement {decision.gesture_label}."
        if decision.gesture_label
        else "Ne propose aucun geste commercial."
    )
    safety_sentence = (
        "Cette réponse peut être envoyée automatiquement. Elle doit être finale, claire et actionnable."
        if decision.auto_send_allowed
        else "Cette réponse doit rester prudente et orienter vers une prise en charge humaine sans promesse risquée."
    )
    prompt = f"""
Rédige une réponse email professionnelle en français pour un client.

Contraintes:
- ton empathique, naturel et précis
- adapte fortement le contenu au mail reçu
- évite les formulations génériques et répétitives
- réponds directement aux points soulevés par le client
- si le client est contrarié, reconnais le problème dès le début
- ne pas promettre un remboursement, un délai ou une action non confirmés
- 120 à 220 mots
- signer avec "{company_signature}"
- entreprise: {company_name}
- {gesture_sentence}
- {safety_sentence}

Client: {sender_name}
Historique client: {json.dumps(customer_record, ensure_ascii=False)}
Analyse: {analysis}
Décision: {decision}
Base de connaissance interne: {knowledge_base or "Aucune information interne fournie"}
Message d'origine:
\"\"\"{original_message}\"\"\"
""".strip()

    try:
        return _invoke_text_model(client, model, prompt).strip()
    except Exception:
        LOGGER.exception("Gemini reply generation failed, using fallback")
        return build_fallback_reply(sender_name, analysis, decision, company_signature)


def build_fallback_reply(
    sender_name: str,
    analysis: AnalysisResult,
    decision: DecisionResult,
    company_signature: str,
) -> str:
    greeting = f"Bonjour {sender_name}," if sender_name else "Bonjour,"
    lines = [
        greeting,
        "",
        f"Nous avons bien pris connaissance de votre message concernant {analysis.issue_summary}.",
        f"Votre demande a été classée avec un niveau d'urgence {analysis.urgency.lower()}.",
    ]
    if decision.gesture_label:
        lines.append(f"Afin de vous apporter une solution concrète, nous vous proposons {decision.gesture_label}.")
    elif not decision.auto_send_allowed:
        lines.append("Votre dossier nécessite une vérification complémentaire par notre équipe avant confirmation définitive.")
    else:
        lines.append("Notre équipe vous apporte un suivi prioritaire et une réponse adaptée à votre situation.")
    lines.extend(["Merci pour votre confiance.", "", company_signature])
    return "\n".join(lines)


def evaluate_auto_send_safety(
    analysis: AnalysisResult,
    *,
    auto_send_enabled: bool,
    allow_auto_send_furious: bool,
) -> tuple[bool, str | None]:
    if not auto_send_enabled:
        return False, "Envoi automatique désactivé dans la configuration."
    if analysis.confidence < 0.75:
        return False, "Confiance IA insuffisante."
    if analysis.risk_level == "ELEVE":
        return False, "Risque métier élevé."
    if analysis.sentiment == "FURIEUX" and not allow_auto_send_furious:
        return False, "Client furieux: validation humaine requise."
    if analysis.intent in {"remboursement"}:
        return False, "Cas de remboursement à valider manuellement."
    return True, None


def load_decision_matrix() -> list[dict[str, Any]]:
    raw_matrix = os.getenv("DECISION_MATRIX_JSON")
    if not raw_matrix:
        return DEFAULT_MATRIX
    try:
        return json.loads(raw_matrix)
    except json.JSONDecodeError:
        LOGGER.exception("DECISION_MATRIX_JSON is invalid, using defaults")
        return DEFAULT_MATRIX


def _invoke_text_model(client: str | None, model: str, prompt: str) -> str:
    if not client:
        raise ValueError("Gemini API key missing")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={client}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    parts = []
    for candidate in data.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                parts.append(text)
    return "\n".join(parts).strip()

def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in model response")
    return text[start : end + 1]
