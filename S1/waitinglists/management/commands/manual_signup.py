from django.core.management.base import BaseCommand

from waitinglists.models import Session
from waitinglists.management.commands.collect_signups import handle_signups

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        session = Session.objects.get(id=179)
        handle_signups(session)