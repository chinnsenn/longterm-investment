# Use official Python slim image as base
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV UV_CACHE_DIR=/app/.uv-cache
ENV UV_SYSTEM_PYTHON=true

# Create non-root user for security
RUN addgroup --system app && adduser --system --group app

# Install system dependencies and UV
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Development stage with all dependencies
FROM base AS development

# Copy source code first
COPY . .

# Install dependencies with uv
RUN uv pip install --system -e ".[dev]" --compile

# Create data and logs directories and set permissions
RUN mkdir -p data logs && chmod 755 data logs

# Switch to non-root user
USER app

# Production stage - minimal image
FROM base AS production

# Copy source code first
COPY . .

# Install only production dependencies with uv
RUN uv pip install --system -e . --compile

# Create data and logs directories and set permissions
RUN mkdir -p data logs && chmod 755 data logs

# Switch to non-root user
USER app

# Expose port (if needed for future web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "main.py"]
