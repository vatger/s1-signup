from django.core.management.base import BaseCommand
from django.utils import timezone

from waitinglists.models import WaitingList


class Command(BaseCommand):
    help = "Monthly command to inform users of waiting list renewal"

    def handle(self, *args, **kwargs):
        inactives = WaitingList.objects.filter(
            completed=False, expiry_date__lt=timezone.now()
        )
        for inactive in inactives:
            print(inactive.first_name + " " + inactive.last_name)
