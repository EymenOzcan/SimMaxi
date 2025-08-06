from django.apps import AppConfig

from django.apps import AppConfig


class EsimConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.esim"


class EsimConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.esim"

    def ready(self):
        import app.esim.signals
