from django.apps import AppConfig


class WaitinglistsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "waitinglists"

    def ready(self):
        import waitinglists.signals
