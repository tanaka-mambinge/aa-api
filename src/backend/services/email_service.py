import json
from dataclasses import dataclass
import asyncio
import smtplib
from email.message import EmailMessage
from urllib import error, request

from backend.config import Settings


@dataclass
class SentEmail:
    to: str
    subject: str
    body: str
    html: str


def _password_reset_text(reset_url: str) -> str:
    return (
        "We received a request to reset your Agent Approvals password.\n\n"
        f"Reset it here: {reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )


def _password_reset_html(reset_url: str) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="en">
  <body style="margin:0;padding:32px 16px;background-color:#eceff3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#16191d;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px;width:100%;background-color:#ffffff;border:1px solid #c8d0da;border-radius:8px;">
            <tr>
              <td style="padding:32px 32px 24px 32px;">
                <div style="display:inline-flex;align-items:center;gap:8px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;letter-spacing:0.2em;color:#9aa2ae;text-transform:uppercase;">
                  &#9679;&nbsp;AGENT APPROVALS
                </div>
                <h1 style="margin:16px 0 8px 0;font-size:20px;line-height:1.3;font-weight:600;color:#16191d;">Reset your password</h1>
                <p style="margin:0;font-size:14px;line-height:1.6;color:#6b7480;">
                  We received a request to reset the password for your Agent Approvals account. Click the button
                  below to choose a new one.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 32px 32px;">
                <a href="{reset_url}"
                   style="display:inline-block;width:100%;box-sizing:border-box;text-align:center;background-color:#16191d;color:#eceff3;font-size:14px;font-weight:600;text-decoration:none;padding:12px 20px;border-radius:8px;">
                  Reset password
                </a>
                <p style="margin:20px 0 0 0;font-size:12px;line-height:1.6;color:#9aa2ae;word-break:break-all;">
                  Or copy this link into your browser:<br />
                  <a href="{reset_url}" style="color:#525c68;">{reset_url}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px;border-top:1px solid #e1e6ec;">
                <p style="margin:0;font-size:12px;line-height:1.6;color:#9aa2ae;">
                  If you did not request this, you can safely ignore this email — your password will not change.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


class MemoryEmailSender:
    def __init__(self):
        self.sent_messages: list[SentEmail] = []

    async def send_password_reset(self, *, to_email: str, reset_url: str) -> None:
        self.sent_messages.append(
            SentEmail(
                to=to_email,
                subject="Reset your Agent Approvals password",
                body=_password_reset_text(reset_url),
                html=_password_reset_html(reset_url),
            )
        )


class SmtpEmailSender:
    def __init__(self, settings: Settings):
        self.host = settings.mail_host
        self.port = settings.mail_port
        self.from_address = settings.mail_from

    async def send_password_reset(self, *, to_email: str, reset_url: str) -> None:
        await asyncio.to_thread(self._send_password_reset_sync, to_email, reset_url)

    def _send_password_reset_sync(self, to_email: str, reset_url: str) -> None:
        message = EmailMessage()
        message["From"] = self.from_address
        message["To"] = to_email
        message["Subject"] = "Reset your Agent Approvals password"
        message.set_content(_password_reset_text(reset_url))
        message.add_alternative(_password_reset_html(reset_url), subtype="html")

        with smtplib.SMTP(self.host, self.port) as smtp:
            smtp.send_message(message)


class ResendEmailSender:
    def __init__(self, settings: Settings):
        self.api_key = settings.resend_api_key
        self.from_address = settings.mail_from

    async def send_password_reset(self, *, to_email: str, reset_url: str) -> None:
        await asyncio.to_thread(self._send_password_reset_sync, to_email, reset_url)

    def _send_password_reset_sync(self, to_email: str, reset_url: str) -> None:
        if not self.api_key:
            raise RuntimeError("RESEND_API_KEY is required when MAIL_TRANSPORT=resend")

        payload = json.dumps(
            {
                "from": self.from_address,
                "to": [to_email],
                "subject": "Reset your Agent Approvals password",
                "text": _password_reset_text(reset_url),
                "html": _password_reset_html(reset_url),
            }
        ).encode("utf-8")

        req = request.Request(
            "https://api.resend.com/emails",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(req, timeout=30) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f"Resend request failed with status {resp.status}")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Resend request failed with status {exc.code}: {detail}"
            ) from exc


def build_email_sender(settings: Settings):
    transport = settings.mail_transport.strip().lower()
    if not transport:
        if settings.app_env == "test":
            transport = "memory"
        elif settings.app_env == "prod":
            transport = "resend"
        else:
            transport = "smtp"

    if transport == "memory":
        return MemoryEmailSender()
    if transport in {"smtp", "maildev"}:
        return SmtpEmailSender(settings)
    if transport == "resend":
        if not settings.resend_api_key:
            raise RuntimeError("RESEND_API_KEY is required when MAIL_TRANSPORT=resend")
        return ResendEmailSender(settings)

    raise RuntimeError(f"Unknown MAIL_TRANSPORT: {settings.mail_transport}")
