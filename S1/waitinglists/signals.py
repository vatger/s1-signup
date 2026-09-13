from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .helpers import send_forum_msg, send_mail
from .models import Session, WaitingList
import os


def queue_new_session_notifications(session_id):
    session = Session.objects.select_related("module").get(pk=session_id)
    message = (
        f"There is a new session available for {session.module.name}. "
        "Find more information in the S1 Centre."
    )
    for signup in WaitingList.objects.filter(
        module=session.module, completed=False
    ).select_related("user"):
        send_forum_msg(
            signup.user.username,
            "New Session Available",
            message,
            "S1 Centre",
            os.getenv("SITE_URL"),
        )
        send_mail(
            signup.user.username,
            "New Session Available",
            message,
            "S1 Centre",
            os.getenv("SITE_URL"),
        )

@receiver(post_save, sender=Session)
def run_on_creation(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(
            lambda: queue_new_session_notifications(instance.pk)
        )
