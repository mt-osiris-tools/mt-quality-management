# Multi-stage build for security and efficiency
# Base image: Python 3.11 slim

# ============================================
# Builder Stage
# ============================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-warn-script-location -r requirements.txt

# ============================================
# Runtime Stage
# ============================================
FROM python:3.11-slim

# Security: Create non-root user
RUN useradd -m -u 1000 -s /bin/bash qms && \
    mkdir -p /app && \
    chown -R qms:qms /app

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder --chown=qms:qms /root/.local /home/qms/.local

# Copy application code
COPY --chown=qms:qms main.py .
COPY --chown=qms:qms src/ ./src/
COPY --chown=qms:qms alembic/ ./alembic/
COPY --chown=qms:qms alembic.ini .

# Switch to non-root user
USER qms

# Add local Python binaries to PATH
ENV PATH=/home/qms/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop"]
