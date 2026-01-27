#!/bin/bash
set -e

# Default Django settings
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-mobilepoint.settings}
echo "Using Django settings: $DJANGO_SETTINGS_MODULE"

# Wait for PostgreSQL to be ready
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
  until nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
  echo "PostgreSQL is up!"
fi

# Run migrations and collectstatic as app user
if [ "$(id -u)" = "0" ]; then
    echo "Running migrations as app user..."
    su -s /bin/bash app -c "python manage.py migrate --noinput"

    echo "Collecting static files..."
    su -s /bin/bash app -c "python manage.py collectstatic --noinput"
else
    echo "Running migrations as current user..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Starting service..."
if [ "$(id -u)" = "0" ]; then
    exec su -s /bin/bash app -c "exec $*"
else
    exec "$@"
fi
