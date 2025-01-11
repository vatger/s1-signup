from django.db import models
from django.contrib.auth.models import User


class Module(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class WaitingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True, blank=True)
    date_completed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.module}"


class Session(models.Model):
    class Language(models.TextChoices):
        ENGLISH = "EN", "English"
        GERMAN = "DE", "German"

    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    capacity = models.IntegerField()
    mentor = models.ForeignKey(User, on_delete=models.CASCADE)
    open_signup = models.BooleanField(default=False)
    attendance_done = models.BooleanField(default=False)
    language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.GERMAN
    )

    def __str__(self):
        return f"{self.module} - {self.datetime.strftime("%d/%m/%y - %H:%M")}Z - {self.mentor.first_name} {self.mentor.last_name}"


class Signup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    waiting_list = models.ForeignKey(
        WaitingList, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.session}"


class Attendance(models.Model):
    class Status(models.TextChoices):
        ATTENDED = "ATT", "Attended"
        ABSENT = "ABS", "Absent"
        EXCUSED = "EXC", "Excused"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    attended = models.CharField(
        max_length=3, choices=Status.choices, default=Status.ATTENDED
    )
    signup = models.OneToOneField(
        Signup, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.session}"


class QuizCompletion(models.Model):
    class QuizID:
        id = (
            (1526, "BASICS"),
            (1527, "DELIVERY"),
            (1525, "GROUND"),
            (1528, "TOWER"),
        )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz_id = models.IntegerField(choices=QuizID.id)
    date_completed = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.quiz_id.__str__()}"
