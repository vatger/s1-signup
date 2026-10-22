from django.contrib import admin

from .models import RosterEntry

@admin.register(RosterEntry)
class RosterEntryAdmin(admin.ModelAdmin):
    search_fields = ("cid__startswith",)
    search_help_text = "Search by CID."