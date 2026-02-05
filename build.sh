#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting server..."
exec gunicorn ngo_project.wsgi:application
