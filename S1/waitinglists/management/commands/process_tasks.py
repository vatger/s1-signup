import json
import logging

from django.core.management.base import BaseCommand

from waitinglists.task_queue import (
    archive_task,
    claim_tasks,
    purge_old_processed_tasks,
)
from waitinglists.tasks import process_task


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process queued background tasks."

    def handle(self, *args, **options):
        purge_old_processed_tasks()
        for task_file in claim_tasks():
            try:
                task = json.loads(task_file.read_text(encoding="utf-8"))
                process_task(task)
                archive_task(task_file, "completed")
            except Exception as exc:
                logger.exception("Queued task failed: %s", task_file)
                archive_task(task_file, "failed", str(exc))
