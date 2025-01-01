nginx -g "daemon on;"

crontab cron_schedule && crond
cd S1 && gunicorn S1.wsgi --bind 127.0.0.1:8016