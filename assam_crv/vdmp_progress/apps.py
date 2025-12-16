from django.apps import AppConfig


class VdmpProgressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vdmp_progress'

    def ready(self):
        import vdmp_progress.signals