from daguerre.widgets import AreaWidget
from daguerre.tests.models import BasicImageModel

from django.contrib import admin
from django.db import models


class BasicImageAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ImageField: {'widget': AreaWidget},
    }


admin.site.register(BasicImageModel, BasicImageAdmin)