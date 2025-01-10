from django.core.management.base import BaseCommand

import os
from dotenv import load_dotenv

from waitinglists.helpers import enrol_and_check_overrides

load_dotenv()


class Command(BaseCommand):
    help = "Command running every minute to sign users up for moodle"

    def handle(self, *args, **kwargs):
        vids = os.listdir("/opt/s1/S1/db/moodle-signup")
        if not vids:
            return
        vid = vids[0]
        enrol_and_check_overrides(vid)
        os.remove(f"/opt/s1/S1/db/moodle-signup/{vid}")
