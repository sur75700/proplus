import aiosmtplib
from email.message import EmailMessage

from .config import settings


async def send_email(to: str, subject: str, html: str) -> bool:
    """
    Sends email in production.

    In local/dev mode, it logs the email payload and returns True so auth/register,
    verify, and password-reset flows do not break because of missing SMTP credentials.
    """
    if settings.email_dev_mode:
        print("============================================================")
        print("📧 PROPLUS EMAIL DEV MODE")
        print("============================================================")
        print(f"TO: {to}")
        print(f"SUBJECT: {subject}")
        print("BODY:")
        print(html)
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
