from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta

import os
from dotenv import load_dotenv

from waitinglists.models import WaitingList
from waitinglists.helpers import send_forum_msg

load_dotenv()


class Command(BaseCommand):
    help = "Monthly command to inform users of waiting list renewal"

    def handle(self, *args, **kwargs):
        next_month = timezone.now() + relativedelta(months=1)
        user_ids = set(
            WaitingList.objects.filter(
                completed=False, expiry_date__month=next_month.month
            ).values_list("user__username", flat=True)
        )
        for id in user_ids:
            send_forum_msg(
                id,
                "Waiting List Renewal",
                "Your waiting list signup is about to expire. Please renew it if you are still interested.",
                "S1 Centre",
                os.getenv("SITE_URL"),
            )
