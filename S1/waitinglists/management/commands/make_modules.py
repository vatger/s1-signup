from django.core.management.base import BaseCommand

from waitinglists.models import Module


class Command(BaseCommand):
    help = "Initial setup to create modules"

    def handle(self, *args, **kwargs):
        Module.objects.create(name="Module 1")
        Module.objects.create(name="Module 3")
        Module.objects.create(name="Module 4")
