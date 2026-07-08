"""Gmail-Tools: Lesen + Entwürfe erstellen.

Bewusst KEIN Sende-Tool und die Scopes enthalten kein ``gmail.send`` – ein
kompromittierter Client kann so auf API-Ebene nicht senden (Leitfaden E/H).
Ein Entwurf hat keine externe Nebenwirkung (nichts verlässt das Postfach) →
Tier 0. Senden wäre Tier 1, existiert hier aber gar nicht.
"""
from __future__ import annotations

import base64
from email.mime.text import MIMEText

from ..security.permission_gateway import EffectCategory
from .base import Tool, ToolResult

# Minimale Scopes – hart durchgesetzt von Google.
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


def build_draft_raw(to: str, subject: str, body: str, sender: str = "me") -> str:
    """Baut eine MIME-Nachricht und kodiert sie base64url (wie von der API erwartet).

    Reine Funktion – ohne Netz testbar.
    """
    msg = MIMEText(body, _charset="utf-8")
    msg["To"] = to
    msg["Subject"] = subject
    if sender and sender != "me":
        msg["From"] = sender
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


class GmailClient:
    """Dünner Wrapper um die Gmail-API. Google-Imports gekapselt."""

    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json") -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service = None

    def _svc(self):
        if self._service is not None:
            return self._service
        try:  # pragma: no cover - nur mit echten Google-Paketen/Token
            import os
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "Gmail-Abhängigkeiten fehlen: `pip install google-api-python-client "
                "google-auth-oauthlib google-auth`."
            ) from exc

        creds = None
        if os.path.exists(self.token_path):  # pragma: no cover
            creds = Credentials.from_authorized_user_file(self.token_path, GMAIL_SCOPES)
        if not creds or not creds.valid:  # pragma: no cover
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w", encoding="utf-8") as fh:
                fh.write(creds.to_json())
        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def list_unread(self, max_results: int = 10) -> list[dict]:  # pragma: no cover
        svc = self._svc()
        res = svc.users().messages().list(userId="me", q="is:unread", maxResults=max_results).execute()
        out = []
        for m in res.get("messages", []):
            full = svc.users().messages().get(userId="me", id=m["id"], format="metadata",
                                              metadataHeaders=["From", "Subject"]).execute()
            headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
            out.append({"id": m["id"], "from": headers.get("From", ""), "subject": headers.get("Subject", "")})
        return out

    def create_draft(self, to: str, subject: str, body: str) -> dict:  # pragma: no cover
        svc = self._svc()
        raw = build_draft_raw(to, subject, body)
        return svc.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()


def build_gmail_tools(client: GmailClient) -> list[Tool]:
    def gmail_list(max_results: int = 10) -> ToolResult:
        msgs = client.list_unread(int(max_results))
        if not msgs:
            return ToolResult(True, "Keine ungelesenen E-Mails.")
        lines = [f"- von {m['from']}: {m['subject']}" for m in msgs]
        return ToolResult(True, "Ungelesene E-Mails:\n" + "\n".join(lines), {"count": len(msgs)})

    def gmail_create_draft(to: str, subject: str, body: str) -> ToolResult:
        draft = client.create_draft(to, subject, body)
        return ToolResult(True, f"Entwurf erstellt (ID {draft.get('id', '?')}). Wird NICHT automatisch gesendet.",
                          {"draft_id": draft.get("id")})

    return [
        Tool(
            name="gmail_list", description="Listet ungelesene E-Mails (nur lesen).",
            effect=EffectCategory.READ,
            parameters={"type": "object", "properties": {"max_results": {"type": "integer"}}},
            run=gmail_list, intent_template="Ungelesene E-Mails auflisten",
        ),
        Tool(
            name="gmail_create_draft",
            description="Erstellt einen E-Mail-Entwurf (sendet NICHT). Jonas prüft und sendet selbst.",
            effect=EffectCategory.SUGGEST,
            parameters={
                "type": "object",
                "properties": {
                    "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
            run=gmail_create_draft, intent_template="E-Mail-Entwurf an {to}: {subject}",
        ),
    ]
