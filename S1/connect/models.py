from django.db import models
from django.contrib.auth.models import User


def get_name(self):
    return self.first_name + " " + self.last_name


User.add_to_class("__str__", get_name)


# Create your models here.
class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    en_preferred = models.BooleanField(default=False)
    subdivision = models.CharField(max_length=10, blank=True, null=True)
    flagged_for_deletion = models.BooleanField(default=False)
    rating = models.IntegerField()

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name
