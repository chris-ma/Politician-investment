# ── Local development / Railway alternative ───────────────────────────────────
# Vercel does not use this Dockerfile — it uses the @vercel/python runtime.
# Use this file for local Docker development or if you deploy to Railway instead.
#
# Local usage:
#   docker build -t au-politicians .
#   docker run -e DATABASE_URL=... -p 8000:8000 au-politicians
#
# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Build dependencies for psycopg2-binary and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Only the shared library is needed at runtime (not headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . .

EXPOSE 8000

# Initialise tables then start the web server.
CMD ["sh", "-c", "python scripts/init_db.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
