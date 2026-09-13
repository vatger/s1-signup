from connect.models import UserDetail

from .helpers import (
    _send_notification_request,
    assign_training_exam_request,
    upgrade_and_add_to_roster,
)


def process_task(task):
    if task["task"] == "send_notification":
        _send_notification_request(**task["payload"])
        return
    if task["task"] == "assign_training_exam":
        if not assign_training_exam_request(**task["payload"]):
            raise RuntimeError("VATEUD did not assign the training exam")
        return
    if task["task"] == "upgrade_user":
        vatsim_id = task["payload"]["vatsim_id"]
        if not upgrade_and_add_to_roster(vatsim_id):
            raise RuntimeError("VATEUD upgrade or roster creation failed")
        UserDetail.objects.filter(user__username=str(vatsim_id)).update(upgraded=True)
        return
    raise ValueError(f"Unknown queued task: {task['task']}")
