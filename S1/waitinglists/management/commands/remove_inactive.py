from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.admin.models import DELETION

from waitinglists.models import WaitingList

from S1.helpers import log_admin_action


class Command(BaseCommand):
    help = "Monthly command to inform users of waiting list renewal"

    def handle(self, *args, **kwargs):
        inactives = WaitingList.objects.filter(
            completed=False, expiry_date__lt=timezone.now()
        )
        for inactive in inactives:
            pass # inactive.delete()
        log_admin_action(
            User.objects.get(id=1000),
            inactive,
            DELETION,
            f"Deleted {inactive.user.username}, {inactive.module.name}, {inactive.date_added}, {inactive.expiry_date}",
        )
