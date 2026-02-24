# Use Python slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal, add more only if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    libnss3 \
    libxss1 \
    libatk1.0-0 \
    libgtk-3-0 \
    libxcomposite1 \
    libxrandr2 \
    libasound2 \
    libxdamage1 \
    libxi6 \
    libxkbcommon0 \
    libxfixes3 \
    libxrender1 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .



# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 10000

# Health check


# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
