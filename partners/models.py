from django.db import models
from django.utils import timezone
import json

# Create your models here.

class NormalizedAddress(models.Model):
    address = models.CharField(max_length=200, db_index=True)



class Partner(models.Model):
    id = models.BigAutoField(primary_key=True)
    data = models.JSONField(default=list)
    idempotency_key = models.CharField(max_length=200, unique=True)
    normalized = models.BooleanField(default=False)
    received_at = models.DateField(default=timezone.now)
    address = models.ForeignKey(NormalizedAddress, on_delete=models.PROTECT, related_name='address', related_query_name='address')

    class Meta:
        ordering = ["-received_at"]



class Listing(models.Model):
    id = models.BigAutoField(primary_key=True)
    dedupe_id = models.CharField(max_length=255, unique=True, db_index=True)
    address = models.ForeignKey(NormalizedAddress, on_delete=models.PROTECT, related_name='address', related_query_name='address')
    lat = models.FloatField()
    lng = models.FloatField()
    price = models.IntegerField()       # In AED
    beds = models.IntegerField()
    baths = models.IntegerField()
    status = models.CharField(max_length=50)
    sources = models.JSONField(default=list) 
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["price", "beds"]),
            models.Index(fields=["updated_at"]),
        ]
        ordering = ["-updated_at"]

