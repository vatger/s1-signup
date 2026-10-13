from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from waitinglists.models import Attendance, Session, Signup
from waitinglists.helpers import notify_confirmation
from functools import partial

@transaction.atomic
def handle_signups(session):
    now = timezone.now()
    remaining = session.capacity - Attendance.objects.filter(session=session).count()
    signups = Signup.objects.filter(session=session).select_related("user").order_by(
        "waiting_list__date_added", "pk"
    )

    for signup in signups:
        if remaining <= 0:
            break
        if Attendance.objects.filter(
            user_id=signup.user_id,
            session__module_id=session.module_id,
            session__datetime__gt=now,
        ).exists():
            continue

        attendance, created = Attendance.objects.get_or_create(
            user_id=signup.user_id,
            session=session,
            defaults={"signup": signup},
        )
        if not created:
            continue

        Signup.objects.filter(
            user_id=signup.user_id,
            session__module_id=session.module_id,
            session__datetime__gt=now,
            attendance__isnull=True,
        ).exclude(session=session).delete()

        remaining -= 1
        transaction.on_commit(partial(notify_confirmation, signup.user, session))

    session.open_signup = True
    session.save(update_fields=["open_signup"])

class Command(BaseCommand):
    help = "Daily command to create Attendances from Signups"

    def handle(self, *args, **kwargs):
        # Get all Sessions that are exactly two days in the future
        sessions = Session.objects.filter(
            datetime__gt=timezone.now() + timezone.timedelta(days=1.5),
            datetime__lt=timezone.now() + timezone.timedelta(days=3),
            open_signup=False,
        ).order_by("datetime", "pk")
        self.stdout.write(f"Found {len(sessions)} sessions.")
        for session in sessions:
            handle_signups(session)
