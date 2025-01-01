from django.contrib import admin
from django.contrib.auth.models import User, Group


from .models import Attendance, Module, Session, Signup, WaitingList


class SessionAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "mentor":
            # Filter users who belong to the "Mentor" group
            mentor_group = Group.objects.filter(name="Mentor").first()
            if mentor_group:
                kwargs["queryset"] = User.objects.filter(groups=mentor_group)
                # Customize the display label in the dropdown
                kwargs["queryset"] = kwargs["queryset"].order_by(
                    "first_name", "last_name"
                )
            else:
                kwargs["queryset"] = (
                    User.objects.none()
                )  # No group found, no users displayed
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Optional: Customize how users are displayed in the dropdown
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(full_name=Concat("first_name", Value(" "), "last_name"))
        return qs


admin.site.register(Attendance)
admin.site.register(Module)
admin.site.register(Session, SessionAdmin)
admin.site.register(Signup)
admin.site.register(WaitingList)
