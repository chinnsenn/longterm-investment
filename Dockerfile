# Use official Python slim image as base
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH=/home/app/.local/bin:$PATH
ENV HOME=/home/app

# Create non-root user for security
RUN addgroup --system app && adduser --system --group app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Development stage with all dependencies
FROM base AS development

# Copy source code first
COPY --chown=app:app . .

# Install dependencies with pip (user install to avoid permission issues)
RUN pip install --user -e ".[dev]"

# Switch to non-root user
USER app

# Create data and logs directories with correct ownership
RUN mkdir -p data logs

# Production stage - minimal image
FROM base AS production

# Copy source code first
COPY --chown=app:app . .

# Install only production dependencies with pip (user install to avoid permission issues)
RUN pip install --user -e .

# Switch to non-root user
USER app

# Create data and logs directories with correct ownership
RUN mkdir -p data logs

# Expose port (if needed for future web interface)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "main.py"]
