# get_model
try:
    # django >= 1.7
    from django.apps import apps
    get_model = apps.get_model
except ImportError:
    # django < 1.7
    from django.db.models import get_model  # flake8: noqa
