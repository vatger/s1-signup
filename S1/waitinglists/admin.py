from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.admin.models import LogEntry
from django import forms
from django.contrib import messages
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import path, reverse


from .models import (
    Attendance,
    Comment,
    Module,
    Session,
    Signup,
    QuizCompletion,
    WaitingList,
)
from .task_queue import list_tasks
from .task_queue import enqueue


class TestNotificationForm(forms.Form):
    user_id = forms.CharField(
        label="VATSIM user ID",
        max_length=20,
        help_text="The user's VATSIM CID / username.",
    )
    title = forms.CharField(max_length=200, initial="Test notification")
    message = forms.CharField(widget=forms.Textarea, max_length=5000)
    via = forms.ChoiceField(
        choices=(
            ("mail", "Mail"),
            ("board.ping", "Forum notification"),
            ("board.ping,mail", "Forum and mail"),
        ),
        initial="mail",
    )
    link_text = forms.CharField(max_length=200, required=False, initial="S1 Centre")
    link_url = forms.URLField(required=False, initial="https://s1.vatger.de")


def task_queue_view(request):
    tasks = list_tasks()
    return render(
        request,
        "admin/waitinglists/task_queue.html",
        {
            **admin.site.each_context(request),
            "title": "Task queue",
            "tasks": tasks,
        },
    )


def test_notification_view(request):
    if request.method == "POST":
        form = TestNotificationForm(request.POST)
        if form.is_valid():
            enqueue(
                "send_notification",
                {
                    "id": form.cleaned_data["user_id"],
                    "title": form.cleaned_data["title"],
                    "message": form.cleaned_data["message"],
                    "link_text": form.cleaned_data["link_text"],
                    "link_url": form.cleaned_data["link_url"],
                    "via": form.cleaned_data["via"],
                },
            )
            messages.success(request, "Test notification queued successfully.")
            return redirect(reverse("admin:waitinglists_task_queue"))
    else:
        form = TestNotificationForm()

    return render(
        request,
        "admin/waitinglists/test_notification.html",
        {
            **admin.site.each_context(request),
            "title": "Send test notification",
            "form": form,
        },
    )


_original_get_urls = admin.site.get_urls


def get_admin_urls():
    custom_urls = [
        path(
            "task-queue/",
            admin.site.admin_view(task_queue_view),
            name="waitinglists_task_queue",
        ),
        path(
            "task-queue/test/",
            admin.site.admin_view(test_notification_view),
            name="waitinglists_test_notification",
        ),
    ]
    return custom_urls + _original_get_urls()


admin.site.get_urls = get_admin_urls


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
