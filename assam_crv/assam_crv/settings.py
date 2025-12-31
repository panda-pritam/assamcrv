"""
Django settings for assam_crv project.

CRITICAL: DLL path configuration MUST be at the very top
"""

import os
import sys

# ============================================================================
# CRITICAL: Configure DLL paths BEFORE any other imports
# This MUST be the first thing after basic imports
# ============================================================================
if os.name == "nt":
    # Get the conda environment path
    conda_env = os.path.dirname(sys.executable)
    
    # CRITICAL: Library\bin MUST be first in PATH for GEOS/GDAL to work
    library_bin = os.path.join(conda_env, 'Library', 'bin')
    
    # Completely rebuild PATH with Library\bin at the very front
    current_path = os.environ.get('PATH', '')
    # Remove library_bin if it already exists anywhere in PATH
    path_parts = [p for p in current_path.split(os.pathsep) if p != library_bin]
    # Put library_bin at the very front
    new_path = library_bin + os.pathsep + os.pathsep.join(path_parts)
    os.environ['PATH'] = new_path
    
    # Add DLL directories (Python 3.8+)
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(library_bin)
        except (FileNotFoundError, OSError):
            pass
    
    # Set GDAL/GEOS environment variables
    gdal_data = os.path.join(conda_env, 'Library', 'share', 'gdal')
    proj_lib = os.path.join(conda_env, 'Library', 'share', 'proj')
    
    if os.path.exists(gdal_data):
        os.environ['GDAL_DATA'] = gdal_data
    if os.path.exists(proj_lib):
        os.environ['PROJ_LIB'] = proj_lib
    
    # Set explicit library paths for Django GIS
    geos_dll = os.path.join(library_bin, 'geos_c.dll')
    gdal_dll = os.path.join(library_bin, 'gdal.dll')
    
    # CRITICAL: Set these BEFORE Django loads
    if os.path.exists(geos_dll):
        os.environ['GEOS_LIBRARY_PATH'] = geos_dll
    if os.path.exists(gdal_dll):
        os.environ['GDAL_LIBRARY_PATH'] = gdal_dll
    
    # CRITICAL: Print debug info to verify paths are set
    # print(f"DEBUG SETTINGS: Python executable: {sys.executable}")
    # print(f"DEBUG SETTINGS: Conda env: {conda_env}")
    # print(f"DEBUG SETTINGS: Library\\bin: {library_bin}")
    # print(f"DEBUG SETTINGS: Library\\bin exists: {os.path.exists(library_bin)}")
    # print(f"DEBUG SETTINGS: geos_c.dll exists: {os.path.exists(geos_dll)}")
    # print(f"DEBUG SETTINGS: gdal.dll exists: {os.path.exists(gdal_dll)}")
    # print(f"DEBUG SETTINGS: PATH starts with: {os.environ['PATH'][:300]}")

# Now safe to import other modules
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings
SECRET_KEY = config('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'accounts',
    'village_profile',
    'training',
    'rescue_equipment',
    'administrator',
    'vdmp_dashboard',
    'vdmp_progress',
    'layers',
    'task_force',
    'field_images',
    'shapefiles',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'assam_crv.middleware.AdminAuthMiddleware',
]

AUTH_USER_MODEL = 'accounts.tblUser'

ROOT_URLCONF = 'assam_crv.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'assam_crv.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'OPTIONS': {
            'options': '-c default_transaction_isolation=serializable'
        },
    },
    'mobile_db': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('MOBILE_DB_NAME'),
        'USER': config('MOBILE_DB_USER'),
        'PASSWORD': config('MOBILE_DB_PASSWORD'),
        'HOST': config('MOBILE_DB_HOST'),
        'PORT': config('MOBILE_DB_PORT', cast=int),
    },
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('as', 'Assamese'),
    ('bn', 'Bengali'), 
    ('brx', 'Bodo'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Max upload size (in bytes)
DATA_UPLOAD_MAX_MEMORY_SIZE = 204857600  
FILE_UPLOAD_MAX_MEMORY_SIZE = 204857600  
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Django GIS Library Paths (set from environment variables configured above)
if os.name == "nt":
    conda_env = os.path.dirname(sys.executable)
    library_bin = os.path.join(conda_env, 'Library', 'bin')
    GEOS_LIBRARY_PATH = os.path.join(library_bin, 'geos_c.dll')
    GDAL_LIBRARY_PATH = os.path.join(library_bin, 'gdal.dll')
    print(f"DEBUG SETTINGS: Setting GEOS_LIBRARY_PATH = {GEOS_LIBRARY_PATH}")
    print(f"DEBUG SETTINGS: Setting GDAL_LIBRARY_PATH = {GDAL_LIBRARY_PATH}")


# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django_error.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'myapp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}