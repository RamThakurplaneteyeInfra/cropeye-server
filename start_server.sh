#!/bin/sh
# Wrapper script to start Gunicorn and filter health check logs

echo '🚀 Starting Django application...'
mkdir -p /app/logs

echo '⏳ Waiting for database connection...'
# Using hosted database - DB_HOST should be set via environment variables
until nc -z -v -w30 "${DB_HOST}" "${DB_PORT:-5432}"; do
  echo "Waiting for database at ${DB_HOST}:${DB_PORT:-5432}..."
  sleep 2
done

echo '✅ Database is up and running!'
echo '🔧 Fixing phone number issues before migrations...'
python fix_phone_before_migrations.py || echo '⚠️  Phone fix script failed, continuing...'
echo '📊 Applying database migrations...'
python manage.py migrate --noinput

echo '📁 Collecting static files...'
python manage.py collectstatic --noinput

echo '🌐 Starting Gunicorn server (health checks filtered from logs)...'

# Start Gunicorn and pipe all output through the filter
# The filter will remove health check access logs but keep error logs
# Use PORT environment variable if set (for Render), otherwise default to 8000
PORT=${PORT:-8000}
exec gunicorn farm_management.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    2>&1 | python3 /app/filter_health_checks.py

