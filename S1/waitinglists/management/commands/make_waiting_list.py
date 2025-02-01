from django.core.management.base import BaseCommand
from waitinglists.models import WaitingList, Module
from django.contrib.auth.models import User
from django.utils import timezone
from time import sleep


class Command(BaseCommand):
    help = "Initial creation of waiting list from csv"

    def handle(self, *args, **kwargs):
        module1 = Module.objects.get(name="Module 4")
        i = 0
        with open("/opt/s1/S1/db/ids.txt") as f:
            for line in f.readlines():
                id = int(line.strip("\n;,"))
                print(id)
                try:
                    user = User.objects.get(username=id)
                    expiry_date = timezone.now() + timezone.timedelta(days=63)
                    expiry_date = expiry_date.replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0
                    )
                    entry = WaitingList(
                        user=user,
                        module=module1,
                        expiry_date=expiry_date,
                    )
                    entry.save()
                    i += 1
                    sleep(1.2)
                except User.DoesNotExist:
                    print(f"User with ID {id} does not exist.")
        self.stdout.write(f"Created {i} entries.")
