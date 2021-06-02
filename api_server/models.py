from django.db import models

class FrozenResource(models.Model):
    hash = models.CharField(max_length=100, null=False)
    data = models.JSONField(default=dict, null=False)
    parent = models.ManyToManyField("self", symmetrical=False)


   