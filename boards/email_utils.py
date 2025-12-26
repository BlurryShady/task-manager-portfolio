import os
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


def _sender_email_from_default() -> str:
    """
    Extract email from DEFAULT_FROM_EMAIL like:
    'Blurry Shady <roruow5@gmail.com>' -> 'roruow5@gmail.com'
    """
    default = getattr(settings, "DEFAULT_FROM_EMAIL", "")
    if "<" in default and ">" in default:
        return default.split("<")[-1].rstrip(">").strip()
    return default.strip() or "noreply@example.com"


def send_brevo_email(
    subject: str,
    text_body: str,
    to_email: str,
    html_body: str | None = None,
) -> None:
    """
    Send email via Brevo HTTP API if BREVO_API_KEY exists,
    otherwise send via Django email backend (SMTP) as multipart (text + html).
    """

    # -----------------------------
    # 1) SMTP / Django backend path
    # -----------------------------
    if not BREVO_API_KEY:
        try:
            from django.core.mail import EmailMultiAlternatives

            from_email = settings.DEFAULT_FROM_EMAIL
            msg = EmailMultiAlternatives(subject, text_body or "", from_email, [to_email])

            # If HTML is provided, attach it so the button/link is clickable.
            if html_body:
                msg.attach_alternative(html_body, "text/html")

            msg.send(fail_silently=False)
            return

        except Exception:
            logger.exception("Failed to send SMTP email to %s", to_email)
            return

    # -----------------------------
    # 2) Brevo HTTP API path
    # -----------------------------
    payload: dict = {
        "sender": {
            "email": _sender_email_from_default(),
            "name": getattr(settings, "SITE_NAME", "Task Manager"),
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
        logger.info("Brevo API response %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
    except Exception:
        logger.exception("Failed to send Brevo email to %s", to_email)
        return
