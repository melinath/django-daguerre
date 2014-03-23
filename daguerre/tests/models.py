from django.db import models

class BasicImageModel(models.Model):
    image = models.ImageField()