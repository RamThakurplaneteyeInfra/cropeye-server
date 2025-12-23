import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# GDAL Settings
# Try to auto-detect GDAL library path
import sys

# Get conda environment paths if using conda
conda_env_paths = []
if 'CONDA_PREFIX' in os.environ:
    conda_prefix = os.environ['CONDA_PREFIX']
    conda_env_paths = [
        os.path.join(conda_prefix, 'Library', 'bin', 'gdal304.dll'),
        os.path.join(conda_prefix, 'Library', 'bin', 'gdal303.dll'),
        os.path.join(conda_prefix, 'Library', 'bin', 'gdal302.dll'),
        os.path.join(conda_prefix, 'Library', 'bin', 'gdal301.dll'),
    ]

gdal_paths = [
    r'C:\OSGeo4W\apps\gdal-dev\bin\gdal-dev312.dll',
    r'C:\OSGeo4W\apps\gdal-dev\bin\gdal-dev311.dll',
    r'C:\OSGeo4W\apps\gdal-dev\bin\gdal-dev310.dll',
    r'C:\OSGeo4W\bin\gdal310.dll',
    r'C:\OSGeo4W\bin\gdal309.dll',
    r'C:\OSGeo4W\bin\gdal308.dll',
    r'C:\OSGeo4W64\bin\gdal310.dll',
    r'C:\OSGeo4W64\bin\gdal309.dll',
    r'C:\OSGeo4W64\bin\gdal308.dll',
] + conda_env_paths

geos_paths = [
    r'C:\OSGeo4W\bin\geos_c.dll',
    r'C:\OSGeo4W64\bin\geos_c.dll',
]
if 'CONDA_PREFIX' in os.environ:
    conda_prefix = os.environ['CONDA_PREFIX']
    geos_paths.extend([
        os.path.join(conda_prefix, 'Library', 'bin', 'geos_c.dll'),
    ])

# Check environment variable first
GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH')
GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH')

# If not set, try to find it
if not GDAL_LIBRARY_PATH:
    for path in gdal_paths:
        if os.path.exists(path):
            GDAL_LIBRARY_PATH = path
            break

if not GEOS_LIBRARY_PATH:
    for path in geos_paths:
        if os.path.exists(path):
            GEOS_LIBRARY_PATH = path
            break

# Load environment variables
# Try to load .env.local first (for development), then .env
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
else:
    load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# ALLOWED_HOSTS - Allow all hosts for local network access (same WiFi)
# For production, set ALLOWED_HOSTS environment variable with specific domains
allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '*')
if allowed_hosts_env == '*':
    ALLOWED_HOSTS = ['*']  # Allow all hosts for local network access
else:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # Enable GeoDjango
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',
    'django_filters',
    'leaflet',  # Remove leaflet
    # 'djgeojson',  # Remove djgeojson
    
    # Local apps
    'users',
    'tasks',
    'equipment',
    'bookings',
    'inventory',
    'vendors',
    'farms',
    'messaging',  # Two-way communication system
    'chatbot',
    'industries',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'users.middleware.JSONExceptionMiddleware',  # Catch exceptions early for API requests
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'farm_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'farm_management.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DB_NAME', 'neoce'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'admin'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Custom authentication backend for phone number login
AUTHENTICATION_BACKENDS = [
    'users.backends.PhoneNumberBackend',  # Phone number authentication
    'django.contrib.auth.backends.ModelBackend',  # Fallback to default
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'EXCEPTION_HANDLER': 'users.exception_handler.custom_exception_handler',
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS settings - Allow all origins for development
CORS_ALLOW_ALL_ORIGINS = True
# Note: When CORS_ALLOW_ALL_ORIGINS is True, CORS_ALLOW_CREDENTIALS must be False
# Browsers don't allow credentials with wildcard origins
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Swagger settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

# Email settings for OTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Use SMTP for real email sending
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Uncomment for development
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '')

# Frontend URL for password reset links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# LEAFLET_CONFIG 
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (28.6139, 77.2090),  # Coordinates for New Delhi, India
    'DEFAULT_ZOOM': 6,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
    'RESET_VIEW': True,
    'TILES': 'http://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    'ATTRIBUTION': '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}

# FastAPI Services URLs
EVENTS_API_URL = os.environ.get('EVENTS_API_URL', 'http://localhost:9000')
SOIL_API_URL = os.environ.get('SOIL_API_URL', 'http://localhost:8002')  # soil.py
ADMIN_API_URL = os.environ.get('ADMIN_API_URL', 'http://localhost:7031')  # Admin.py
ET_API_URL = os.environ.get('ET_API_URL', 'http://localhost:8009')    # ET.py
FIELD_API_URL = os.environ.get('FIELD_API_URL', 'http://localhost:8003')  # field.py

# Hosted Render backend URL for plot fetching
HOSTED_BACKEND_URL = os.environ.get('HOSTED_BACKEND_URL', 'https://cropeye-server-1.onrender.com')

# WhatsApp OTP Configuration (Twilio)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', '')

# OTP Configuration
WHATSAPP_OTP_ENABLED = os.environ.get('WHATSAPP_OTP_ENABLED', 'True').lower() == 'true'
EMAIL_OTP_FALLBACK = os.environ.get('EMAIL_OTP_FALLBACK', 'True').lower() == 'true'
