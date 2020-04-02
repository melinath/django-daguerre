# Settings for testing django-daguerre.

import os

PROJECT_DIR = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

DB = os.environ.get('DB')
if DB == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'daguerre_test',
            'USER': 'root',
            'TEST_CHARSET': 'utf8',
            'TEST_COLLATION': 'utf8_general_ci',
        }
    }
elif DB == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'daguerre_test',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': 5432,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(PROJECT_DIR, 'db.sl3'),
        }
    }

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
USE_L10N = False
USE_TZ = True

MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media/')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static/')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = 'test_key'

# Django < 1.9
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# Django 1.9+
# https://docs.djangoproject.com/en/1.9/ref/templates/upgrading/
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'test_project.urls'
WSGI_APPLICATION = 'test_project.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'daguerre',
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
