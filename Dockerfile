# Netflix OCA Locator - Ephemeral Docker Container
# Multi-stage build for minimal image size

# Build stage
FROM python:3.11-alpine AS builder

# Install system dependencies required for building
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies and build the package
RUN uv venv && \
    uv pip install -e . && \
    uv pip install --no-deps .

# Runtime stage
FROM python:3.11-alpine AS runtime

# Install runtime system dependencies
RUN apk add --no-cache \
    whois \
    curl \
    ca-certificates

# Create non-root user for security
RUN addgroup -g 1000 netflix && \
    adduser -D -s /bin/sh -u 1000 -G netflix netflix

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application
COPY --from=builder /app/src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV NETFLIX_OCA_LOG_LEVEL="INFO"

# Create output directory with correct permissions
RUN mkdir -p /app/output && \
    chown -R netflix:netflix /app

# Switch to non-root user
USER netflix

# Set working directory
WORKDIR /app

# Create entrypoint script
COPY --chown=netflix:netflix docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=1 \
    CMD python -c "import netflix_oca_locator; print('OK')" || exit 1

# Default command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["--help"]

# Metadata labels
LABEL org.opencontainers.image.title="Netflix OCA Locator"
LABEL org.opencontainers.image.description="Ephemeral container to locate Netflix Open Connect Appliances"
LABEL org.opencontainers.image.version="2.1.0"
LABEL org.opencontainers.image.authors="Esteban Carisimo"
LABEL org.opencontainers.image.source="https://github.com/yourusername/Netflix-OCA-Servers-Locator"
LABEL org.opencontainers.image.licenses="MIT"