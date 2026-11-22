# One image for the demo and for institutional servers. The data (database, uploads, photographs) belongs on a
# mounted volume: set DATA_DIR=/data and DATABASE_URL=sqlite:////data/herbar.db, and mount a volume at /data.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Migrations first; a demo instance (DEMO_MODE=true) then seeds itself if its database is empty.
# Hosts such as Railway set PORT; the proxy in front of the app terminates HTTPS.
CMD ["sh", "-c", "python -m alembic upgrade head && python -m app.demo seed --if-empty && exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
