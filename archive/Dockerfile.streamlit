# Multi-stage Dockerfile for Word Document Chatbot
# Supports both backend and frontend in separate build targets

# =============================================================================
# Base Python Image
# =============================================================================
FROM python:3.11-slim as python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user with home directory
RUN groupadd -r appuser && \
    useradd -r -g appuser -m -d /home/appuser appuser && \
    chown -R appuser:appuser /home/appuser

# =============================================================================
# Backend Stage
# =============================================================================
FROM python-base as backend

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Create necessary directories
RUN mkdir -p /app/temp && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose backend port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Frontend Stage
# =============================================================================
FROM python-base as frontend

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code and configuration
COPY frontend/ ./frontend/
COPY .env.example .env

# Make entrypoint executable
RUN chmod +x ./frontend/entrypoint.sh

# Set ownership of /app to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Set default environment variables (can be overridden in docker-compose.yml)
ENV BACKEND_URL=http://backend:8000 \
    BASE_URL_PATH= \
    STREAMLIT_PORT=8501 \
    SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_CONFIG_DIR=/app/.streamlit

# Run frontend using entrypoint script
ENTRYPOINT ["./frontend/entrypoint.sh"]
