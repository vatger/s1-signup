#!/bin/sh
set -e

# Collect static files
cd /opt/training/training
python manage.py collectstatic --noinput

nginx -g "daemon on;"

crontab cron_schedule && crond
cd S1 && gunicorn S1.wsgi --bind 127.0.0.1:8016