from typing import List
from partners.models import Listing
from datetime import datetime, timezone


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

class PartnerAAdaptor(PartnerAdaptor):

    
    def get_idempotency_key_data(self) -> list:
        keys = []
        for item in self.data:
            dt = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            iso = dt.astimezone(timezone.utc).isoformat()
            keys.append((f'A-{item['external_id']-{iso}}', self.get_data()))
        return keys
    

class PartnerBAdaptor(PartnerAdaptor):

    def get_idempotency_key_data(self) -> list:
        keys = []
        for item in self.data:
            dt = datetime.fromisoformat(item["ts"])
            iso = dt.astimezone(timezone.utc).isoformat()
            keys.append((f'B-{item['ext_id']-{iso}}', self.get_data()))
        return keys
