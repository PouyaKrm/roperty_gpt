from abc import ABC, abstractmethod
import hashlib
from django.db import models
from django.utils import timezone
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import re

from partners.adapters import compute_dedupe_id, to_iso_utc

# Create your models here.

class NormalizedAddress(models.Model):
    address = models.CharField(max_length=200, db_index=True)



class Partner(models.Model):
    id = models.BigAutoField(primary_key=True)
    data = models.JSONField()
    lat = models.FloatField(null=True)
    lon = models.FloatField(null=True)
    idempotency_key = models.CharField(max_length=200, unique=True)
    normalized = models.BooleanField(default=False)
    received_at = models.DateField(default=timezone.now)
    address = models.ForeignKey(NormalizedAddress, on_delete=models.PROTECT)
    dedupe_key = models.CharField(max_length=200, db_index=True)
    

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

    @abstractmethod
    def get_lat(self):
        pass

    @abstractmethod
    def get_lon(self):
        pass

    def get_dedupe_id(self):
        return compute_dedupe_id(self.get_address(), self.get_lat(), self.get_lon())


    @abstractmethod
    def get_ts(self) -> str:
        pass
    
    @abstractmethod
    def to_listing(self) -> Listing:
        pass
    

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
    
    def get_lat(self):
        return self.lat
    
    def get_lon(self):
        return self.lon
    
    def to_listing(self):
        event_time = to_iso_utc(self.updated)

        dedupe_id = compute_dedupe_id(self.get_address(), self.lat, self.lon)

        return Listing(
            dedupe_id=dedupe_id,
            lat=self.lat,
            lng=self.lon,
            price=self.price_aed,
            beds=self.beds,
            baths=self.baths,
            status=self.status.lower(),
            updated_at=event_time,
            sources=[f"A:{self.get_external_id()}"],
            version=1,
        )


    
   
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
    
    def get_lat(self):
        return self.location.get("lat")
    
    def get_lon(self):
        return self.location.get("lon")
    
    def to_listing(self):
        event_time = to_iso_utc(self.get_ts())
        lat, lng = self.location["lat"], self.location["lon"]

        dedupe_id = compute_dedupe_id(self.addr, lat, lng)

        price_aed = self.price_fils // 100

        state_map = {
            "active": "for_sale",
            "inactive": "off_market",
            "sold": "sold",
        }
        status = state_map.get(self.state.lower(), "off_market")

        return Listing(
            dedupe_id=dedupe_id,
            lat=lat,
            lng=lng,
            price=price_aed,
            beds=self.br,
            baths=self.ba,
            status=status,
            updated_at=event_time,
            sources=[f"B:{self.get_external_id()}"],
            version=1,
        )



def to_partner_list_data_class_from_data(data) -> List[PartnerBase]:
    partners: List[PartnerBase] = []
    for d in data:
        if d['partner'] == 'A':
            partners = partners + [PartnerAListing(**li, partner='A') for li in d['listings']]
        elif d['partner'] == 'B':
            partners = partners + [PartnerBListing(**li, partner='B') for li in d['listings']]
    return partners
    
def to_partner_data_class_from_data(data) -> PartnerBase:
        return PartnerAListing(**data) if data['partner'] == 'A' else PartnerBListing(**data)
