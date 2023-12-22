from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ClusterDetail(models.Model):
    cloud_id = models.CharField(max_length=128, null=False)
    elastic_user = models.CharField(max_length=32, null=False)
    elastic_password = models.CharField(max_length=32, null=False)

    def __str__(self):
        return f"{self.cloud_id}"
