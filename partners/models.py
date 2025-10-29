from abc import ABC, abstractmethod
import hashlib
from django.db import models
from django.utils import timezone
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict
import re

# Create your models here.

class NormalizedAddress(models.Model):
    address = models.CharField(max_length=200, db_index=True)



class Partner(models.Model):
    id = models.BigAutoField(primary_key=True)
    data = models.JSONField()
    idempotency_key = models.CharField(max_length=200, unique=True)
    normalized = models.BooleanField(default=False)
    received_at = models.DateField(default=timezone.now)
    address = models.ForeignKey(NormalizedAddress, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-received_at"]



class Listing(models.Model):
    id = models.BigAutoField(primary_key=True)
    dedupe_id = models.CharField(max_length=255, unique=True, db_index=True)
    address = models.ForeignKey(NormalizedAddress, on_delete=models.PROTECT)
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



from dataclasses import dataclass
from datetime import datetime


@dataclass
class PartnerBase(ABC):
   
    partner: str

    @abstractmethod
    def get_ts_str(self) -> str:
        pass

    @abstractmethod
    def get_external_id(self) -> str:
        pass

    @abstractmethod
    def get_address(self) -> str:
        pass

    def get_ts(self) -> str:
        ts_str = self.get_ts_str().replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str).astimezone(timezone.utc)
        return dt.isoformat()
    
    

    def idempotency_key(self) -> str:
        event_time = self.get_ts()
        raw = f"{self.partner}:{self.get_external_id()}:{event_time}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _normalize_address(address):
        ABBREVIATIONS = {
            r'\bboul\.?\b': 'boulevard',
            r'\bblvd\.?\b': 'boulevard',
            r'\bt1\b': 'tower 1',
            r'\bt2\b': 'tower 2',
        }
        normalized = address.strip().lower()
    
   
        for pattern, replacement in ABBREVIATIONS.items():
            normalized = re.sub(pattern, replacement, normalized)
        
    
        normalized = re.sub(r'\(.*?\)', '', normalized)
        
    
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized

@dataclass
class PartnerAListing(PartnerBase):
    id: str
    address: str
    lat: float
    lon: float
    price_aed: int
    beds: int
    baths: int
    status: str
    updated: str

    def __post_init__(self):
        self.partner = "A"

    def get_ts_str(self) -> str:
        return self.updated

    def get_external_id(self) -> str:
        return self.id

    def get_address(self):
        return _normalize_address(self.address)

    def get_ts(self) -> str:
        ts_str = self.get_ts_str().replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str).astimezone(timezone.utc)
        return dt.isoformat()

@dataclass
class PartnerBListing(PartnerBase):
    ext_id: str
    addr: str
    location: dict
    price_fils: int
    br: int
    ba: int
    state: str
    ts: str 

    def __post_init__(self):
        self.partner = "B"

    def get_ts_str(self) -> str:
        return self.ts

    def get_external_id(self) -> str:
        return self.ext_id

    def get_address(self):
        return _normalize_address(self.addr)

    def get_ts(self) -> str:
        dt = datetime.fromisoformat(self.get_ts_str())
        iso = dt.astimezone(timezone.utc).isoformat()
        return iso