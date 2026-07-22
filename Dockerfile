FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose server port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000

# Launch server
CMD ["python", "main.py"]
