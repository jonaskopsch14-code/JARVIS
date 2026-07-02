"""Gmail (Phase 3): lesen, Entwürfe vorbereiten, senden — mit Sicherheitsstufen.

  gmail_list_unread   Stufe 1 (lesen)
  gmail_prepare_draft Stufe 2 (Entwurf anlegen — verschickt NICHTS)
  gmail_send          Stufe 3 (verschickt in deinem Namen — explizite Bestätigung)

OAuth-Einrichtung (einmalig, Phase 3):
  1. Google-Cloud-Projekt → Gmail API aktivieren → OAuth-Client (Desktop) anlegen.
  2. client_secret als  <DatenOrdner>/gmail_credentials.json  ablegen.
  3. Beim ersten Aufruf öffnet sich der Browser-Login; Token wird gespeichert.
"""

from __future__ import annotations

import base64
from email.mime.text import MIMEText
from pathlib import Path

from . import skill
from ..security import Risk

# von main aus Config gesetzt:
DATA_DIR = Path.home() / "Jarvis"
SCOPES = ["https://www.googleapis.com/auth/gmail.modify",
          "https://www.googleapis.com/auth/gmail.compose",
          "https://www.googleapis.com/auth/gmail.send"]


def _service():
    """Baut den Gmail-API-Client (lazy). Wirft mit klarer Meldung, wenn Setup fehlt."""
    from google.oauth2.credentials import Credentials  # lazy
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    token_path = Path(DATA_DIR) / "gmail_token.json"
    cred_path = Path(DATA_DIR) / "gmail_credentials.json"
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not cred_path.exists():
                raise RuntimeError(
                    f"Gmail nicht eingerichtet: lege {cred_path} an (OAuth-Client-Secret).")
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


@skill(
    name="gmail_list_unread",
    description="Listet die neuesten ungelesenen E-Mails (Absender + Betreff).",
    parameters={"type": "object", "properties": {
        "count": {"type": "integer", "description": "Anzahl (Standard 5)"}}},
    risk=Risk.AUTO,
)
def gmail_list_unread(count: int = 5) -> str:
    try:
        svc = _service()
        res = svc.users().messages().list(
            userId="me", q="is:unread", maxResults=max(1, count)).execute()
        msgs = res.get("messages", [])
        if not msgs:
            return "Keine ungelesenen E-Mails."
        out = []
        for m in msgs:
            full = svc.users().messages().get(
                userId="me", id=m["id"], format="metadata",
                metadataHeaders=["From", "Subject"]).execute()
            hdrs = {h["name"]: h["value"] for h in full["payload"]["headers"]}
            out.append(f"{hdrs.get('From', '?')}: {hdrs.get('Subject', '(kein Betreff)')}")
        return "Ungelesen: " + " | ".join(out)
    except Exception as exc:  # noqa: BLE001
        return f"Gmail-Abruf fehlgeschlagen: {exc}"


def _raw(to: str, subject: str, body: str) -> dict:
    msg = MIMEText(body, _charset="utf-8")
    msg["to"] = to
    msg["subject"] = subject
    return {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}


@skill(
    name="gmail_prepare_draft",
    description="Bereitet einen E-Mail-Entwurf vor (verschickt nichts).",
    parameters={"type": "object", "properties": {
        "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
        "required": ["to", "subject", "body"]},
    risk=Risk.CONFIRM,
    confirm_prompt="Soll ich diesen E-Mail-Entwurf im Postfach anlegen?",
)
def gmail_prepare_draft(to: str, subject: str, body: str) -> str:
    try:
        svc = _service()
        svc.users().drafts().create(
            userId="me", body={"message": _raw(to, subject, body)}).execute()
        return f"Entwurf an {to} angelegt (Betreff: {subject}). Nicht gesendet."
    except Exception as exc:  # noqa: BLE001
        return f"Entwurf fehlgeschlagen: {exc}"


@skill(
    name="gmail_send",
    description="Sendet eine E-Mail im Namen des Nutzers.",
    parameters={"type": "object", "properties": {
        "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
        "required": ["to", "subject", "body"]},
    risk=Risk.EXPLICIT,
    confirm_prompt="ACHTUNG: Diese E-Mail wird jetzt wirklich verschickt.",
)
def gmail_send(to: str, subject: str, body: str) -> str:
    try:
        svc = _service()
        svc.users().messages().send(userId="me", body=_raw(to, subject, body)).execute()
        return f"E-Mail an {to} gesendet (Betreff: {subject})."
    except Exception as exc:  # noqa: BLE001
        return f"Senden fehlgeschlagen: {exc}"
