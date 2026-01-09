# Use official Python slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install immich-autotag from PyPI
RUN pip install --no-cache-dir immich-autotag

# Create a non-root user for security (optional but recommended)
RUN useradd -m autotaguser
USER autotaguser

# Set working directory
WORKDIR /home/autotaguser

# Default command (can be overridden)
CMD ["immich-autotag", "--help"]
