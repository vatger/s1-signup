from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    en_preferred = models.BooleanField(default=False)
    module_2_completed = models.BooleanField(default=False)
    subdivision = models.CharField(max_length=10, blank=True, null=True)
    rating = models.IntegerField()

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name
