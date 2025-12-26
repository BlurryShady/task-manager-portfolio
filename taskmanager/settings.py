"""
Django settings for taskmanager project.
"""

from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

# -------------------------
# Base
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: str = "false") -> bool:
    """
    Reads boolean-ish environment variables safely.
    Accepts: 1/true/yes/on (case-insensitive) as True.
    """
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def split_csv(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


# -------------------------
# Security
# -------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", "true")


# -------------------------
# Hosts / CSRF
# -------------------------
ALLOWED_HOSTS = split_csv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")

# Heroku injects this automatically (safe to include if present)
# (Not required for custom domain, but harmless and helps when opening herokuapp domain)
if heroku_host := os.getenv("HEROKU_APP_NAME"):
    ALLOWED_HOSTS.append(f"{heroku_host}.herokuapp.com")

CSRF_TRUSTED_ORIGINS = split_csv(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:8000,"
    "http://localhost:8000,"
    "https://tasks.blurryshady.dev",
)


# -------------------------
# Application definition
# -------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "boards",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "taskmanager.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "boards.context_processors.analytics",
            ],
        },
    },
]

WSGI_APPLICATION = "taskmanager.wsgi.application"


# -------------------------
# Database
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# -------------------------
# Password validation
# -------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# -------------------------
# Internationalization
# -------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# -------------------------
# Static / Media
# -------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise storage (recommended on Heroku)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}


# -------------------------
# Security headers (Heroku-friendly)
# -------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = (not DEBUG) and env_bool("DJANGO_SECURE_SSL_REDIRECT", "true")


# -------------------------
# Auth redirects
# -------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "workspace_list"
LOGOUT_REDIRECT_URL = "login"


# -------------------------
# Email / notifications (Brevo SMTP)
# -------------------------
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Task Manager <noreply@taskmanager.local>",
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", "true")

SITE_NAME = "Task Manager"


# -------------------------
# Analytics / Telemetry
# -------------------------
PLAUSIBLE_DOMAIN = os.getenv("PLAUSIBLE_DOMAIN", "")
PLAUSIBLE_SCRIPT = os.getenv("PLAUSIBLE_SCRIPT", "https://plausible.io/js/script.js")
ANALYTICS_ENABLED = bool(PLAUSIBLE_DOMAIN)

ENABLE_TELEMETRY = env_bool("ENABLE_TELEMETRY", "true")
