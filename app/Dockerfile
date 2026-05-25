# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/opt/poetry/bin:$PATH"

# Copy dependency specifications
COPY pyproject.toml ./

# Generate requirements and install dependencies
# We use --without-hashes to avoid dependency resolution hash conflicts
RUN poetry run pip install --upgrade pip \
    && poetry export --without-hashes -f requirements.txt -o requirements.txt \
    && pip install --no-cache-dir --user -r requirements.txt

# Final Stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
# Copy application code
COPY app/ ./app/
COPY src/ ./src/
COPY configs/ ./configs/
COPY scripts/ ./scripts/

# Define PATH to include local user-installed bin
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose API port
EXPOSE 8000

# Run FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
