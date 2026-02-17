FROM python:3.11-slim

# Prevent Python buffering
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (required for cryptography)
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY requirements-backend.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy project files
COPY . .

# Run Gunicorn with increased timeout
CMD ["gunicorn", "worksight_server.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "120"]
