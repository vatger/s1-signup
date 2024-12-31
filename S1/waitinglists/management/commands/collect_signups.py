from django.core.management.base import BaseCommand
from django.utils import timezone
from waitinglists.models import Attendance, Session, Signup
from waitinglists.helpers import send_forum_msg

import os
from dotenv import load_dotenv

load_dotenv()


def handle_signups(session: Session):
    try:
        signups = Signup.objects.filter(session=session).order_by(
            "waiting_list__date_added"
        )
        # Choose signups to capacity
        signups = signups[: session.capacity]
        for signup in signups:
            Attendance.objects.update_or_create(
                user=signup.user, session=session, signup=signup
            )
            send_forum_msg(
                signup.user.username,
                "Confirmed Signup",
                f"Your signup for the session {session} has been confirmed.",
                "S1 Centre",
                os.getenv("SITE_URL"),
            )
        session.open_signup = True

    except Session.DoesNotExist:
        print(f"Session with ID {session.id} does not exist.")


class Command(BaseCommand):
    help = "Daily command to create Attendances from Signups"

    def handle(self, *args, **kwargs):
        # Get all Sessions that are exactly two days in the future
        sessions = Session.objects.filter(
            datetime__gt=timezone.now() + timezone.timedelta(days=1.5),
            datetime__lt=timezone.now() + timezone.timedelta(days=3),
        )
        self.stdout.write(f"Found {len(sessions)} sessions.")
        for session in sessions:
            handle_signups(session)
