# =============================================================================
# Multi-stage Dockerfile for CS AI FTE
# Stage 1 (builder): installs Python dependencies
# Stage 2 (runtime): minimal image with app code
# =============================================================================

# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies needed to build Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a local directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install only runtime system libraries (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY . .

# Create non-root user for security
RUN useradd -r -s /bin/false csfte && chown -R csfte:csfte /app
USER csfte

# Expose API port
EXPOSE 8000

# Default command: start FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
