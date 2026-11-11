# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=5

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl tesseract-ocr poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
      --index-url https://download.pytorch.org/whl/cpu \
      --extra-index-url https://pypi.org/simple \
      torch

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m spacy download en_core_web_sm

# Pre-download ML models at build time so the API/worker don't need
# internet access or pay the download cost on first use. Hugging Face
# caches them under /root/.cache/huggingface, which persists in the image.
COPY scripts/prefetch_models.py /app/scripts/prefetch_models.py
RUN --mount=type=cache,target=/root/.cache/pip \
    python /app/scripts/prefetch_models.py

COPY . .
RUN mkdir -p /app/resumes

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
