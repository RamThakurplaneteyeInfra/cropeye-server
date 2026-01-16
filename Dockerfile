# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV DJANGO_SETTINGS_MODULE=farm_management.settings_production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        gettext \
        gdal-bin \
        libgdal-dev \
        python3-gdal \
        binutils \
        netcat-traditional \
        libproj-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

# Install Python dependencies
COPY requirements_production.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create directories for media, static files, and logs
RUN mkdir -p /app/media /app/staticfiles /app/logs

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health/ || exit 1

# Run the application
CMD ["/bin/sh", "-c", "\
    echo '🚀 Starting Django application...' && \
    mkdir -p /app/logs && \
    echo '⏳ Waiting for database connection...' && \
    until nc -z -v -w30 \"${DB_HOST:-db}\" 5432; do \
      echo \"Waiting for database at ${DB_HOST:-db}:5432...\"; \
      sleep 2; \
    done && \
    echo '✅ Database is up and running!' && \
    echo '📊 Applying database migrations...' && python manage.py migrate --noinput && \
    echo '📁 Collecting static files...' && python manage.py collectstatic --noinput && \
    echo '🌐 Starting Gunicorn server...' && exec gunicorn farm_management.wsgi:application --bind 0.0.0.0:8001 --workers 3 --timeout 120 --access-logfile - --error-logfile - \
"]
