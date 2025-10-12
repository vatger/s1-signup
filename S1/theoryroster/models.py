from django.db import models

class RosterEntry(models.Model):
    cid = models.IntegerField(primary_key=True)
