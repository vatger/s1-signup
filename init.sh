#!/bin/sh
set -e

# Collect static files
cd /opt/s1/S1
python manage.py collectstatic --noinput

nginx -g "daemon on;"

crontab cron_schedule && crond
cd /opt/s1/S1 && gunicorn S1.wsgi --bind 127.0.0.1:8016