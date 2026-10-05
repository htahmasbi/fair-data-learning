# syntax=docker/dockerfile:1
# Multi-stage: build wheels in one stage, slim runtime in the other.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# --- deps layer (cached unless requirements.txt changes) ---
FROM base AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- runtime stage ---
FROM base AS runtime

# Run as non-root (security best practice)
RUN useradd --create-home appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Only the code + model + config needed at inference time.
# NOTE: models/model.pkl is DVC-tracked; run `dvc pull` before `docker build`.
COPY src/ ./src/
COPY params.yaml ./
COPY models/ ./models/
COPY metrics.json ./metrics.json

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]