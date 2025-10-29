from typing import List
from partners.models import Listing
from datetime import datetime, timezone
import re

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
    
   

class PartnerAdaptor:

    def __init__(self, data: List[dict]):
        self.data = data


    def get_idempotency_key_data(self) -> list:
        raise NotImplementedError("method not implemeneted") 

    def get_data(self):
        return self.data
    
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

    
    def get_idempotency_key_data(self) -> list:
        keys = []
        for item in self.data:
            address = self._normalize_address(item['address'])
            dt = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            iso = dt.astimezone(timezone.utc).isoformat()
            keys.append((f'A-{item['external_id']-{iso}}', self.get_data(), address))
        return keys
    

class PartnerBAdaptor(PartnerAdaptor):

    def get_idempotency_key_data(self) -> list:
        keys = []
        for item in self.data:
            address = self._normalize_address(item['addr'])
            dt = datetime.fromisoformat(item["ts"])
            iso = dt.astimezone(timezone.utc).isoformat()
            keys.append((f'B-{item['ext_id']-{iso}}', self.get_data(), address))
        return keys
