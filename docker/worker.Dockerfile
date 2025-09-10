# Base image: slim Python 3.11 runtime
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code (worker needs same app code as API)
COPY app /app/app

# Default command: run Celery worker
CMD ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"]
