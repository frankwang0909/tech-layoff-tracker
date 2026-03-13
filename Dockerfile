# ─────────────────────────────────────────────────────
#  Stage 1: Build — Run the data pipeline
# ─────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY scraper/ scraper/
COPY analysis/ analysis/
COPY visualization/ visualization/
COPY main.py .

# Run the pipeline (scrape → process → generate chart)
RUN python main.py

# ─────────────────────────────────────────────────────
#  Stage 2: Serve — Lightweight runtime image
# ─────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="Frank Wang"
LABEL description="Tech Layoff Tracker — Interactive Dashboard"

WORKDIR /app

# Copy only what we need at runtime
COPY --from=builder /app/data/ data/
COPY --from=builder /app/visualization/ visualization/
COPY server.py .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["python", "server.py", "--port", "8080"]
