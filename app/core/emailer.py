import re
from email.message import EmailMessage

import aiosmtplib

from .config import settings


TOKEN_QUERY_RE = re.compile(r"([?&]token=)[^\"'\s<>&]+", re.IGNORECASE)
TOKEN_WORD_RE = re.compile(r"(?i)(token=)[^\"'\s<>&]+")
LONG_SECRET_RE = re.compile(r"\b[A-Za-z0-9_-]{32,}\b")


def redact_email_body(html: str) -> str:
    """
    Redacts high-risk token values from local/dev email logs.

    The real email body is still sent unchanged in production mode.
    This function is only for safe development logging.
    """
    redacted = TOKEN_QUERY_RE.sub(lambda match: f"{match.group(1)}[REDACTED]", html)
    redacted = TOKEN_WORD_RE.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
    redacted = LONG_SECRET_RE.sub("[REDACTED]", redacted)
    return redacted


async def send_email(to: str, subject: str, html: str) -> bool:
    """
    Sends email in production.

    In local/dev mode, it logs a redacted email preview and returns True so
    auth/register, verify, and password-reset flows do not break because of
    missing SMTP credentials.
    """
    if settings.email_dev_mode:
        print("============================================================")
        print("📧 PROPLUS EMAIL DEV MODE")
        print("============================================================")
        print(f"TO: {to}")
        print(f"SUBJECT: {subject}")
        print("BODY:")
        print(redact_email_body(html))
        print("============================================================")
        return True

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("This email requires an HTML-capable email client.")
    msg.add_alternative(html, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_pass,
        start_tls=True,
    )

    return True
