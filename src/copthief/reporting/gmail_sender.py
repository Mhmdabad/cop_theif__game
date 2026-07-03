"""Gmail-API delivery client using token-based OAuth (issue #30).

Authentication uses a downloaded client secret (``credentials.json``) and a
stored OAuth token (``token.json``). No password is ever stored in code or
config (PLAN ADR-7; PRD §3.7).
"""

from __future__ import annotations

import base64
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailSender:
    """Thin wrapper around the Gmail API for sending the game report."""

    def __init__(
        self,
        credentials_path: str | Path = "credentials.json",
        token_path: str | Path = "token.json",
    ) -> None:
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)

    def _load_credentials(self) -> Credentials:
        """Load or refresh OAuth credentials, persisting the token to disk."""
        creds: Credentials | None = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if creds is None or not creds.valid:
            if creds is not None and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json(), encoding="utf-8")

        return creds

    def _service(self) -> Any:
        return build("gmail", "v1", credentials=self._load_credentials())

    def send_report(self, to_email: str, subject: str, report_json: str) -> None:
        """Send ``report_json`` as the entire email body.

        Assignment §9: the body must contain ONLY the structured JSON report —
        no free text — so the grading system can parse it automatically. A
        plain-text single-part message keeps the raw payload unambiguous.
        """
        message = EmailMessage()
        message.set_content(report_json)
        message["To"] = to_email
        message["From"] = "me"
        message["Subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        try:
            self._service().users().messages().send(userId="me", body={"raw": raw}).execute()
        except HttpError as exc:
            raise RuntimeError(f"Failed to send Gmail report: {exc}") from exc
