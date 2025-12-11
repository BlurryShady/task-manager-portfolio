"""Lightweight activity logging helpers."""

from __future__ import annotations

from typing import Any, Optional

from django.conf import settings

from .models import ActivityLog


def _get_client_ip(request) -> Optional[str]:
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_activity(request, action: str, **metadata: Any) -> None:
    """Persist a user/action pair plus useful request metadata."""
    if not getattr(settings, "ENABLE_TELEMETRY", True):
        return

    ActivityLog.objects.create(
        user=(
            request.user
            if getattr(request, "user", None) and request.user.is_authenticated
            else None
        ),
        action=action,
        metadata=metadata,
        request_path=getattr(request, "path", "")[:255],
        ip_address=_get_client_ip(request),
        user_agent=(
            request.META.get("HTTP_USER_AGENT", "") if request else ""
        )[:255],
    )
