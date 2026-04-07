# ============================================================
# SafetyGuard X — Dockerfile
# HuggingFace Spaces compatible (port 7860)
# Build:  docker build -t safetyguard-x .
# Run:    docker run -p 7860:7860 safetyguard-x
# ============================================================

FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user

WORKDIR /home/user/app

COPY --chown=user requirements.txt .

RUN pip install --upgrade pip --no-cache-dir \
 && pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

USER user

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]