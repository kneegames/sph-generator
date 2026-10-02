# Use Python 3.11 slim base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for weasyprint
# Note: libgdk-pixbuf2.0-0 is replaced by libgdk-pixbuf-xlib-2.0-0 in newer Debian
RUN apt-get update && apt-get install -y \
    python3-cairo \
    python3-gi \
    gir1.2-pango-1.0 \
    gir1.2-gtk-3.0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Use Procfile for command (or specify directly)
CMD ["python", "sph_generator.py"]