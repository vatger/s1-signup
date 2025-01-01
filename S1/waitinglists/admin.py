from django.contrib import admin
from django.contrib.auth.models import User, Group


from .models import Attendance, Module, Session, Signup, WaitingList


class SessionAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mentor":
            mentor_group = Group.objects.filter(name="Mentor").first()
            if mentor_group:
                kwargs["queryset"] = User.objects.filter(groups=mentor_group).order_by(
                    "first_name", "last_name"
                )
            else:
                kwargs["queryset"] = User.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name}"


admin.site.register(Attendance)
admin.site.register(Module)
admin.site.register(Session, SessionAdmin)
admin.site.register(Signup)
admin.site.register(WaitingList)
