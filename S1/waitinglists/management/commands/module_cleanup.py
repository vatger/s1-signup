from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from waitinglists.models import Module, QuizCompletion, WaitingList
from waitinglists.views import module_2_completion


class Command(BaseCommand):
    help = "Weekly command to check whether module 2 quizzes have not been completed"

    def handle(self, *args, **kwargs):
        result = []
        # Get users that have completed Module 1 but neither Module 3 or 4
        mod1 = Module.objects.get(name="Module 1")
        mod3 = Module.objects.get(name="Module 3")
        mod4 = Module.objects.get(name="Module 4")

        mod_1_users = set(
            WaitingList.objects.filter(module=mod1, completed=True).values_list(
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
            if timezone.now() - module_1_completion_date < timezone.timedelta(days=40):
                continue
            module_2_completion(User.objects.get(username=user), fetch=True)
            completions = list(
                QuizCompletion.objects.filter(user__username=user).order_by(
                    "date_completed"
                )
            )
            match len(completions):
                case 0:
                    # If time since completion of Module 1 is greater than 40 days, save user to result
                    if (timezone.now() - module_1_completion_date).days > 40:
                        result.append(user)
                case 1:
                    # If difference between completion of Module 1 and the only quiz completion is greater than 40 days, save user to result
                    if (
                        completions[0].date_completed - module_1_completion_date
                    ).days > 40:
                        result.append(user)
                case _:
                    # If difference between last two quiz completions is greater than 40 days, save user to result
                    if (
                        completions[-1].date_completed - completions[-2].date_completed
                    ).days > 40:
                        result.append(user)
        for user in result:
            obj = User.objects.get(username=user)
            obj.userdetail.flagged_for_deletion = True
            obj.userdetail.save()
