"""
URL configuration for assam_crv project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')), 
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('village_profile.urls')),
    path('', include('training.urls')),
    path('', include('rescue_equipment.urls')),
    path('administrator/', include('administrator.urls')),
    path('', include('vdmp_dashboard.urls')),
    path('', include('vdmp_progress.urls')),
    path('', include('layers.urls')),
    path('', include('task_force.urls')),
    path('api/', include('field_images.urls')),  
    path('', include('dashboard.urls')),      
)

urlpatterns += [
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]

# 👇 Add this for media files (only in development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
