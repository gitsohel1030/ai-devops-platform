# ── Stage 1: Builder ──────────────────────────────────────
FROM python:3.10-slim AS builder
 
WORKDIR /app
 
COPY app/requirements.txt .
 
# Install to /install instead of /root/.local
# /root/.local is only accessible by root
# /install is a neutral path accessible by any user
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
 
# ── Stage 2: Final image ──────────────────────────────────
FROM python:3.10-slim
 
WORKDIR /app
 
# Copy installed packages from builder — from /install not /root/.local
COPY --from=builder /install /usr/local
 
# Copy application code
COPY app/ .
 
# Environment variables
ENV MODEL_VERSION=v2
ENV AWS_REGION=ap-south-1
ENV MODEL_S3_BUCKET=mlflow-artifacts-608827180555
ENV MODEL_S3_KEY=""
 
# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
 
EXPOSE 8000
 
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
