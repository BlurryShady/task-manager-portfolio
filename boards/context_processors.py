from django.conf import settings


def analytics(request):
    return {
        "ANALYTICS_ENABLED": getattr(settings, "ANALYTICS_ENABLED", False),
        "PLAUSIBLE_DOMAIN": getattr(settings, "PLAUSIBLE_DOMAIN", ""),
        "PLAUSIBLE_SCRIPT": getattr(settings, "PLAUSIBLE_SCRIPT", ""),
        "SITE_NAME": getattr(settings, "SITE_NAME", "Task Manager"),
    }
