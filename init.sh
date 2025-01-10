nginx -g "daemon on;"

crontab cron_schedule && crond
#cd S1 && gunicorn S1.wsgi --bind 127.0.0.1:8016
cd S1 && python -m uvicorn S1.asgi:application