crontab cron_schedule && crond
cd S1 && gunicorn S1.wsgi --bind 0.0.0.0:8016