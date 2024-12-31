from django.contrib import admin

from .models import Attendance, Module, Session, Signup, WaitingList

# Register your models here.

admin.site.register(Attendance)
admin.site.register(Module)
admin.site.register(Session)
admin.site.register(Signup)
admin.site.register(WaitingList)
