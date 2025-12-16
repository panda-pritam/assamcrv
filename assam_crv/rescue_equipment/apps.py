from django.apps import AppConfig


class RescueEquipmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rescue_equipment'

    def ready(self):
        import rescue_equipment.signals