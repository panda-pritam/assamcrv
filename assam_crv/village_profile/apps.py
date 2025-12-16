from django.apps import AppConfig


class VillageProfileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'village_profile'
    
    def ready(self):
        import village_profile.signals