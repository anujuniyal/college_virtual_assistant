# College Virtual Assistant (EduBot)

This project runs as a Flask application using the **application factory + blueprints** architecture.

## Running locally (Windows / PowerShell)

1. Create and activate a virtualenv, then install dependencies:

```bash
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

2. Run the canonical app:

```bash
$env:FLASK_ENV="development"
python wsgi.py
```

Open `http://localhost:5000/` (it redirects to `/auth/login`).

## Deployment (host)

- **Canonical entrypoint**: `wsgi:app` (already used by `Procfile`, `Dockerfile`, and `render.yaml`)
- Set environment variables:
  - `FLASK_ENV=production`
  - `SECRET_KEY=<strong random value>`
  - `DATABASE_URL=<postgres connection string>`
  - `TELEGRAM_BOT_TOKEN=<telegram bot token>`

## Telegram bot (webhook)

The webhook endpoint is:

- `POST /telegram/webhook`

To activate the webhook after deployment, set:

- `TELEGRAM_BOT_TOKEN`
- `PUBLIC_BASE_URL` (example: `https://your-app.onrender.com`)

Then run:

```bash
python activate_telegram_bot.py
```

Notes:
- Telegram **requires a public HTTPS URL** for webhooks. Localhost will not work unless you tunnel it (ngrok, cloudflared, etc.) and set `PUBLIC_BASE_URL` / `TELEGRAM_WEBHOOK_URL` accordingly.
- Legacy/experimental runners (`run_complete_app.py`, `run_working_app.py`) are intentionally blocked unless `ALLOW_LEGACY_RUNNERS=1`.

