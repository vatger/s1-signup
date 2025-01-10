nginx -g "daemon on;"

crontab cron_schedule && crond
cd S1 && python -m uvicorn S1.asgi:application