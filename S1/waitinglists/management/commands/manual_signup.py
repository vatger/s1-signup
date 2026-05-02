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
                f"""Your signup for the session {session} has been confirmed.
                The session will be held on the VATGER Teamspeak. 
                Please check beforehand if you can access the server.
                More information can be found in the knowledge base.""",
                "S1 Centre",
                os.getenv("SITE_URL"),
            )
        session.open_signup = True
        session.save()

    except Session.DoesNotExist:
        print(f"Session with ID {session.id} does not exist.")


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        session = Session.objects.get(id=179)
        handle_signups(session)
