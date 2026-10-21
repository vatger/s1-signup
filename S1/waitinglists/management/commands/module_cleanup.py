from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from waitinglists.models import Module, QuizCompletion, WaitingList
from waitinglists.views import module_2_completion
import requests


class Command(BaseCommand):
    help = "Command to check whether module 2 quizzes have not been completed. Runs every other day(ish)."

    def handle(self, *args, **kwargs):
        result = []
        # Get users that have completed Module 1 but neither Module 3 or 4
        mod1 = Module.objects.get(name="Module 1")
        mod3 = Module.objects.get(name="Module 3")
        mod4 = Module.objects.get(name="Module 4")

        mod_1_users = set(
            WaitingList.objects.filter(
                module=mod1,
                completed=True,
                user__userdetail__flagged_for_deletion=False,
            ).values_list(
                "user__username", flat=True
            )
        )
        mod_3_users = set(
            WaitingList.objects.filter(module=mod3, completed=True).values_list(
                "user__username", flat=True
            )
        )
        mod_4_users = set(
            WaitingList.objects.filter(module=mod4, completed=True).values_list(
                "user__username", flat=True
            )
        )
        users = mod_1_users - mod_3_users - mod_4_users
        for user in users:
            module_1_completion_date = WaitingList.objects.get(
                module=mod1, user__username=user
            ).date_completed
            if module_1_completion_date is None:
                self.stderr.write(f"module_cleanup: Skipping {user}: Module 1 completion date is missing.")
                continue
            if timezone.now() - module_1_completion_date <= timezone.timedelta(days=31):
                continue
            try:
                _, completed = module_2_completion(User.objects.get(username=user), fetch=True)
            except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                self.stderr.write(f"module_cleanup:: Skipping {user}: Moodle check failed ({exc}).")
                continue
            if completed:
                continue
            completions = list(
                QuizCompletion.objects.filter(user__username=user).order_by(
                    "date_completed"
                )
            )
            last_progress = module_1_completion_date
            if completions:
                last_progress = max(last_progress, completions[-1].date_completed)
            if timezone.now() - last_progress > timezone.timedelta(days=31):
                result.append(user)
        for user in result:
            obj = User.objects.get(username=user)
            obj.userdetail.flagged_for_deletion = True
            obj.userdetail.save()
