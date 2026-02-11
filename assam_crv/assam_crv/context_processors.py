from django.conf import settings


def geoserver_url(request):
    return {"GEOSERVER_URL": getattr(settings, "GEOSERVER_URL", "")}
