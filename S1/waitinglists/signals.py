from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Session, WaitingList
from .helpers import send_forum_msg

import os
from dotenv import load_dotenv

load_dotenv()


@receiver(post_save, sender=Session)
def run_on_creation(sender, instance, created, **kwargs):
    if created:
        list_signups = WaitingList.objects.filter(
            module=instance.module, completed=False
        )
        for signup in list_signups:
            send_forum_msg(
                signup.user.username,
                "New Session Available",
                f"There is a new session available for {instance.module.name}. Find more information in the S1 Centre.",
                "S1 Centre",
                os.getenv("SITE_URL"),
            )
