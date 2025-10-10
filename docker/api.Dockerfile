# Base image: slim Python 3.11 runtime
FROM python:3.11-slim

# Install curl (for debugging and API verification)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code and Alembic migrations
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Default command: run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
