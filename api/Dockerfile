FROM python:3.12-slim

# Install system dependencies for geo libraries
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install uv

WORKDIR /app

# Copy requirements and install via uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# The application code will be mounted as a volume during development
