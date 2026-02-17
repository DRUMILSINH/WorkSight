from pathlib import Path
import os
from dotenv import load_dotenv
import pymysql
pymysql.install_as_MySQLdb()

# =========================
# Base Directory
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# Security (DEV MODE)
# =========================

load_dotenv()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DEBUG = os.getenv("DEBUG") == "True"

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# =========================
# Installed Applications
# =========================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'monitoring',
]


# =========================
# Middleware
# =========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =========================
# URLs / WSGI
# =========================
ROOT_URLCONF = 'worksight_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'worksight_server.wsgi.application'


# =========================
# Database (MySQL)
# =========================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv("DB_NAME", "worksight_db"),
        'USER': os.getenv("DB_USER", "worksight_user"),
        'PASSWORD': os.getenv("DB_PASSWORD", "strongpassword"),
        'HOST': os.getenv("DB_HOST", "127.0.0.1"),
        'PORT': os.getenv("DB_PORT", "3306"),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# =========================
# Password Validation
# =========================
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


# =========================
# Localization
# =========================
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True


# =========================
# Static Files
# =========================
STATIC_URL = 'static/'


# =========================
# Default PK Type
# =========================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
