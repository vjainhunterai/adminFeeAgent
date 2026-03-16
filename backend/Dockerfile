# =========================================================
# Backend Dockerfile — FastAPI + Uvicorn (production)
# =========================================================
# WHAT THIS DOES:
#   1. Starts from a small Python 3.11 image
#   2. Installs only the Python packages we need
#   3. Copies the ENTIRE repo (so backend/ can reach prompts/)
#   4. Runs uvicorn with 2 worker processes
# =========================================================

FROM python:3.11-slim

# --- OS-level deps needed by pymysql / pandas ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl openssh-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Install Python deps first (cached layer) ---
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# --- Copy full repo so config.py can read ../prompts/ ---
COPY . /app

WORKDIR /app/backend

EXPOSE 8000

# --- Health check — Docker restarts container if this fails ---
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# --- Run with 2 workers (good for a t3.medium) ---
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
