#!/bin/sh

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

exec "$@"