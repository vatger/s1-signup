from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry


from .models import (
    Attendance,
    Comment,
    Module,
    Session,
    Signup,
    QuizCompletion,
    WaitingList,
)


class WaitingListAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "module",
        "date_added",
        "completed",
        "expiry_date",
        "date_completed",
    )  # Display in list view
    list_filter = ("completed", "module")  # Add filters for better usability
    search_fields = (
        "user__first_name",
        "user__last_name",
        "module__name",
    )  # Allow searching
    ordering = ("-date_added",)  # Order by most recent first

    fields = (
        "user",
        "module",
        "date_added",
        "completed",
        "expiry_date",
        "date_completed",
    )  # Fields in form view


class SessionAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name="Mentor").exists():
            return ("open_signup",)  # "attendance_done",
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


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = (
        "action_time",
        "user",
        "content_type",
        "object_repr",
        "action_flag",
        "change_message",
    )
    list_filter = ("user", "action_flag")
    search_fields = ("object_repr", "change_message")

    def has_add_permission(self, request):
        return False  # Prevent manual addition


admin.site.register(Attendance)
admin.site.register(Comment)
admin.site.register(Module)
admin.site.register(Session, SessionAdmin)
admin.site.register(Signup)
admin.site.register(QuizCompletion)
admin.site.register(WaitingList, WaitingListAdmin)
