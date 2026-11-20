from django.contrib import admin
from .models import UserDetail

@admin.register(UserDetail)
class UserDetailAdmin(admin.ModelAdmin):
    search_fields = (
        "user__username__startswith",
        "user__first_name",
        "user__last_name",
    )
    search_help_text = "Search by CID or name."
