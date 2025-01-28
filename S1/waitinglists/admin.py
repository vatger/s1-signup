from django.contrib import admin
from django.contrib.auth.models import User, Group


from .models import (
    Attendance,
    Comment,
    Module,
    Session,
    Signup,
    QuizCompletion,
    WaitingList,
)


class SessionAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name="Mentor").exists():
            return ("attendance_done", "open_signup")
        return super().get_readonly_fields(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mentor":
            # Filter users who belong to the "Mentor" group
            mentor_group = Group.objects.filter(name="Mentor").first()
            if mentor_group:
                kwargs["queryset"] = User.objects.filter(groups=mentor_group)
            else:
                kwargs["queryset"] = (
                    User.objects.none()
                )  # No group found, no users displayed
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Attendance)
admin.site.register(Comment)
admin.site.register(Module)
admin.site.register(Session, SessionAdmin)
admin.site.register(Signup)
admin.site.register(QuizCompletion)
admin.site.register(WaitingList)
