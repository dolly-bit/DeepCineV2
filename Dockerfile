# DeepCine FastAPI API image for Google Cloud Run.
# Build from the repository root: gcloud builds submit --tag IMAGE_URL

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# FAISS and PyTorch rely on the OpenMP runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# Copy only backend source. Secrets, virtual environments, and local model
# artifacts are excluded by the repository-root .dockerignore.
COPY backend/ ./

# Cloud Run injects PORT (normally 8080). run.py binds to 0.0.0.0.
CMD ["python", "run.py"]
