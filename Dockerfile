# Use official Python slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1


# Instalar git para soporte GitPython
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install immich-autotag from PyPI
RUN pip install --no-cache-dir immich-autotag

# Create a non-root user for security (optional but recommended)
RUN useradd -m autotaguser
USER autotaguser

# Set working directory
WORKDIR /home/autotaguser

# Ensure ~/.local/bin is in PATH for user-installed scripts
ENV PATH="/home/autotaguser/.local/bin:$PATH"

# Default command (can be overridden)
CMD ["immich-autotag", "--help"]
