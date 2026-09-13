from .helpers import _send_notification_request


def process_task(task):
    if task["task"] == "send_notification":
        _send_notification_request(**task["payload"])
        return
    raise ValueError(f"Unknown queued task: {task['task']}")
