import os
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


def send_brevo_email(
    subject: str,
    text_body: str,
    to_email: str,
    html_body: str | None = None,
) -> None:
    """
    Send an email via Brevo HTTP API.
    Falls back to Django's send_mail if no API key is configured.
    """
    if not BREVO_API_KEY:
        from django.core.mail import send_mail
        logger.warning("BREVO_API_KEY not set; falling back to Django send_mail.")
        send_mail(subject, text_body, settings.DEFAULT_FROM_EMAIL, [to_email])
        return

    payload: dict = {
        "sender": {
            "email": settings.DEFAULT_FROM_EMAIL.split("<")[-1].rstrip(">").strip(),
            "name": settings.SITE_NAME,
        },
        "to": [{"email": to_email}],
        "subject": subject,
    }

    if text_body:
        payload["textContent"] = text_body
    if html_body:
        payload["htmlContent"] = html_body

    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    try:
        resp = requests.post(BREVO_ENDPOINT, json=payload, headers=headers, timeout=10)
        print("Brevo API response", resp.status_code, resp.text)
        resp.raise_for_status()
    except Exception:
        logger.exception("Failed to send Brevo email to %s", to_email)
        return
