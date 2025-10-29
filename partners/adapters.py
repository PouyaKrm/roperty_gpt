from typing import List
from partners.models import Listing, Partner
from datetime import datetime, timezone
import re
import hashlib

class Normalizer():
    def __init__(self, data):
        self.data = data
        adaptors: List[PartnerAdaptor] = []
        for item in data:
            if item['partner'] == 'A':
                adaptors.append(PartnerAAdaptor(item['listings']))
            else:
                adaptors.append(PartnerBAdaptor(item['listings']))
        self._adaptors = adaptors

    def get_idempotency_key_data(self):
        kv = []
        for adaptor in self._adaptors:
            kv = adaptor.get_idempotency_key_data()
        return kv
    
    
class ListingAdaptor:
    def __init__(self, partners):
        self.partners = partners
        adaptors: List[PartnerAdaptor] = []
        for item in partners:
            data = item.data
            if item['partner'] == 'A':
                adaptors.append(PartnerAAdaptor(item['listings']))
            else:
                adaptors.append(PartnerBAdaptor(item['listings']))
            self._adaptors = adaptors
        def get_listings(self):
            result = []
            for a in adaptors:
                result = result + a.get_listing()

class PartnerAdaptor:

    

    def get_idempotency_key_data(self) -> list:
        raise NotImplementedError("method not implemeneted") 
    
    def _get_dedupe_id(self, partner: Partner) -> str:
            raw = partner.data
            dedupe_key = f"{partner.address.address}:{round(raw['lat'], 4)}:{round(raw['lon'], 4)}"
            return hashlib.sha1(dedupe_key.encode("utf-8")).hexdigest()
    
    def get_listing(self, partner)-> List[Listing]:
        raise NotImplementedError("method not implemeneted") 



    def _normalize_address(self, address):
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


class PartnerAAdaptor(PartnerAdaptor):

    
    def get_idempotency_key_data(self, data_ite) -> list:
        keys = []
        for item in self.data:
            address = self._normalize_address(item['address'])
            dt = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            iso = dt.astimezone(timezone.utc).isoformat()
            keys.append((f'A-{item['external_id']-{iso}}', item, address, iso))
        return keys
    
    def get_listing(self, partner: Partner)-> List[Listing]:
        listings = []
        
        raw = partner.data
        dedupe_id = self._get_dedupe_id(p)
        listing = Listing(
            dedupe_id=dedupe_id,
            lat=raw["lat"],
        lng=raw["lon"],
        price=raw["price_aed"],
        beds=raw["beds"],
        baths=raw["baths"],
        status=raw["status"].lower(),
        updated_at=p.received_at,
        sources=[f"A:{raw['id']}"],
        version=1,
            )

        return listing



class PartnerBAdaptor(PartnerAdaptor):

    def get_idempotency_key_data(self) -> list:
        keys = []
        for item in self.data:
            address = self._normalize_address(item['addr'])
            dt = datetime.fromisoformat(item["ts"])
            iso = dt.astimezone(timezone.utc).isoformat()
            keys.append((f'B-{item['ext_id']-{iso}}', item, address))
        return keys

    def get_listing(self, partner: List[Partner])-> List[Listing]:
        listings = []
        for p in partners:
            raw = p.data
            lat = raw["location"]["lat"]
            lng = raw["location"]["lon"]
            price = raw["price_fils"] // 100
            state_map = {
            "active": "for_sale",
            "inactive": "off_market",
            "sold": "sold"
        }
            status = state_map.get(raw["state"].lower(), "off_market")
            dedupe_id = self._get_dedupe_id(p)
            listing = Listing(
                dedupe_id=dedupe_id,
                lat=lat,
                lng=lng,
                price=price,
                beds=raw["br"],
                baths=raw["ba"],
                status=status,
                updated_at=p.received_at,
             sources=[f"B:{raw['ext_id']}"],
                version=1,
            )
            listings.append(listing)

        return listings
