import json
import logging

from django.core.management.base import BaseCommand

from waitinglists.task_queue import (
    archive_task,
    claim_tasks,
    purge_old_processed_tasks,
    schedule_retry,
    MAX_RETRIES,
)
from waitinglists.tasks import process_task


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process queued background tasks."

    def handle(self, *args, **options):
        purge_old_processed_tasks()
        for task_file in claim_tasks():
            task = {}
            try:
                task = json.loads(task_file.read_text(encoding="utf-8"))
                process_task(task)
                archive_task(task_file, "completed")
            except Exception as exc:
                logger.exception("Queued task failed: %s", task_file)
                attempts = task.get("attempts", 0)
                if task and attempts < MAX_RETRIES:
                    schedule_retry(task_file, str(exc))
                else:
                    archive_task(task_file, "failed", str(exc), attempts=attempts)
