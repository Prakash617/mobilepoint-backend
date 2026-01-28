#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-mobilepoint.settings}
echo "Using Django settings: $DJANGO_SETTINGS_MODULE"

# Run migrations only for backend service
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