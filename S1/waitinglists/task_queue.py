import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.conf import settings


QUEUE_DIR = Path(os.getenv("TASK_QUEUE_DIR", settings.BASE_DIR.parent / "task_queue"))
PROCESSED_DIR = QUEUE_DIR / "processed"
STALE_PROCESSING_SECONDS = 30 * 60
PROCESSED_RETENTION_SECONDS = 7 * 24 * 60 * 60
RETRY_DELAY_SECONDS = 60 * 60
MAX_RETRIES = 3


def enqueue(task_name, payload):
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    task_id = uuid.uuid4().hex
    temporary = QUEUE_DIR / f".{task_id}.tmp"
    queued = QUEUE_DIR / f"{task_id}.json"
    temporary.write_text(
        json.dumps({"task": task_name, "payload": payload}),
        encoding="utf-8",
    )
    os.replace(temporary, queued)


def claim_tasks(limit=50):
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    for processing in QUEUE_DIR.glob("*.processing"):
        if time.time() - processing.stat().st_mtime > STALE_PROCESSING_SECONDS:
            os.replace(processing, processing.with_suffix(".json"))

    claimed = []
    for queued in sorted(QUEUE_DIR.glob("*.json")):
        try:
            task = json.loads(queued.read_text(encoding="utf-8"))
            next_attempt_at = task.get("next_attempt_at")
            if next_attempt_at and datetime.fromisoformat(next_attempt_at) > datetime.now(timezone.utc):
                continue
        except (OSError, ValueError, TypeError):
            pass
        processing = queued.with_suffix(".processing")
        try:
            os.replace(queued, processing)
        except FileNotFoundError:
            continue
        claimed.append(processing)
        if len(claimed) >= limit:
            break
    return claimed


def archive_task(task_file, status, error=None, **metadata):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    try:
        task = json.loads(task_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        task = {"task": "Invalid task file", "payload": {}, "error": str(exc)}
    task.update(
        {
            "status": status,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    if error:
        task["error"] = error
    task.update(metadata)
    archived = PROCESSED_DIR / task_file.name.replace(".processing", ".json")
    temporary = PROCESSED_DIR / f".{archived.stem}.tmp"
    temporary.write_text(json.dumps(task), encoding="utf-8")
    os.replace(temporary, archived)
    task_file.unlink(missing_ok=True)


def schedule_retry(task_file, error):
    task = json.loads(task_file.read_text(encoding="utf-8"))
    retry_number = task.get("attempts", 0) + 1
    next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=RETRY_DELAY_SECONDS)
    task["attempts"] = retry_number
    task["next_attempt_at"] = next_attempt_at.isoformat()

    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    retry_id = uuid.uuid4().hex
    temporary = QUEUE_DIR / f".{retry_id}.tmp"
    queued = QUEUE_DIR / f"{retry_id}.json"
    temporary.write_text(json.dumps(task), encoding="utf-8")
    os.replace(temporary, queued)
    archive_task(
        task_file,
        "retry_scheduled",
        error,
        attempts=retry_number,
        next_attempt_at=next_attempt_at.isoformat(),
    )


def list_tasks():
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    for task_file in QUEUE_DIR.glob("*.json"):
        tasks.append(_read_task(task_file, "queued"))
    for task_file in QUEUE_DIR.glob("*.processing"):
        tasks.append(_read_task(task_file, "processing"))
    for task_file in PROCESSED_DIR.glob("*.json"):
        tasks.append(_read_task(task_file, None))
    return sorted(tasks, key=lambda task: task["filename"], reverse=True)


def purge_old_processed_tasks():
    cutoff = time.time() - PROCESSED_RETENTION_SECONDS
    deleted = 0
    for task_file in PROCESSED_DIR.glob("*.json"):
        if task_file.stat().st_mtime < cutoff:
            task_file.unlink()
            deleted += 1
    return deleted


def _read_task(task_file, default_status):
    try:
        task = json.loads(task_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        task = {"task": "Invalid task file", "error": str(exc)}
    task["filename"] = task_file.name
    task.setdefault("status", default_status)
    task["payload_json"] = json.dumps(
        task.get("payload", {}), indent=2, ensure_ascii=False
    )
    return task
