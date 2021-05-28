from django.db import models

class FrozenResource(models.Model):
    hash = models.CharField(primary_key=True ,max_length=100)
    data = models.JSONField(default=dict)
    parent = models.ManyToManyField("this", related_name="frs")
