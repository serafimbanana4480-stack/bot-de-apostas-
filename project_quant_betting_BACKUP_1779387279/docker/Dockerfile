# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (e.g., for building some C-extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy poetry config if available, or just use pip
COPY requirements.txt .

# Install python dependencies
# Using a mock requirements file structure for now
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install fastapi uvicorn pydantic pydantic-settings xgboost pandas numpy scikit-learn httpx redis sqlalchemy asyncpg shap prometheus_client python-telegram-bot

# Copy project files
COPY . .

# Expose API port
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
