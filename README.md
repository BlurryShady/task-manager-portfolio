# Task Manager

A modern, glassmorphic Trello-style productivity app built with Django.
Users can create workspaces, invite collaborators, organize boards with custom columns and manage tasks through an intuitive drag-and-drop interface.
The project includes email verification, welcome flows, task assignment, priorities, due dates and lightweight backend telemetry for auditing actions.

## Highlights

- **Workspaces & Boards** – Users can structure their personal or team projects using boards, each containing customizable workflow columns and tasks.
- **Task engine** – Priorities, due dates, assignees and drag-and-drop reordering.
- **Collaboration** – Invite members by username or email and archive unwanted tasks.
- **Auth polish** – Email+username sign-up, verification links, welcome emails and custom login feedback for inactive accounts.
- **Telemetry & Activity Logging** – All entries are stored in the ActivityLog model and accessible via Django admin.
- **Modern UI** – Responsive glass UI, sticky top bar with @username pill and keyboard shortcuts.

## Tech Stack
**Backend**

Python 3.12+

Django 5.2

SQLite (local)

Optional PostgreSQL for production

Built-in email system with overrideable SMTP settings

Custom context processors

Whitenoise for static files in production


**Frontend**

HTML, Django Templates

CSS (custom glassmorphic theme)

Vanilla JavaScript (drag-and-drop, shortcuts)


**Other**

Lightweight telemetry via ActivityLog model

Secure deployment-ready settings structure

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows (or `source .venv/bin/activate` on macOS/Linux)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/`.

## Environment Variables

| Variable | Description | Default |
| --- | --- | --- |
| `SECRET_KEY` | Django secret key for crypto and sessions | value in settings (override in prod) |
| `DEBUG` | Set to `0`/`False` in production | `True` |
| `ALLOWED_HOSTS` | Comma separated hostnames | empty |
| `EMAIL_BACKEND` | Django email backend path | `django.core.mail.backends.console.EmailBackend` |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS/SSL` | SMTP settings for activation + welcome emails | unset |
| `DEFAULT_FROM_EMAIL` | Sender name/address | `Task Manager <noreply@taskmanager.local>` |
| `ENABLE_TELEMETRY` | Toggle server-side `ActivityLog` writes (`0` to disable) | `1` |
| `SITE_NAME` | Branding string for emails/meta | `Task Manager` |

## Email Verification Flow

1. User signs up with username + email.
2. Account is created inactive and an activation link is sent.
3. Visiting the link activates the user, sends a welcome email, logs them in and records telemetry for both steps.
4. Attempting to log in before verification shows a helpful validation error.

To send real emails, switch to your SMTP/Testmail credentials by updating the email environment variables above.


## Project Structure (Simplified)

```
boards/          # App: models, forms, views, templates, telemetry helpers
static/          # CSS + JS bundle (drag-and-drop, styles)
taskmanager/     # Project settings + URL routing
```

Key templates live under `boards/templates`, grouped by feature (workspaces, auth, registration emails). Static assets sit under `static/css/style.css` and `static/js/app.js`.

## Testing & Linting

The project ships with Django’s default test runner. Add tests to `boards/tests.py` and execute:

```bash
python manage.py test boards
```

## Deployment Notes

- Switch to Postgres/MySQL by updating `DATABASES` in `taskmanager/settings.py` or via `DATABASE_URL` if you add `dj-database-url`.
- Configure HTTPS, CSRF trusted origins, and a production-ready email backend.


I've created this to showcase in my portfolio. You can see how it looks at tasks.blurryshady.dev
