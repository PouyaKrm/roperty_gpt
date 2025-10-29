from dataclasses import asdict
from typing import List
from partners.models import NormalizedAddress, Partner, PartnerAListing, PartnerBListing, PartnerBase
from django.utils.dateparse import parse_datetime

def add_new_record(batch_data):
    partners: List[PartnerBase] = []
    for d in batch_data:
        if d['partner'] == 'A':
            partners = partners + [PartnerAListing(**li, partner='A') for li in d['listings']]
        elif d['partner'] == 'B':
            partners = partners + [PartnerBListing(**li, partner='B') for li in d['listings']]

    
    keys = [p.idempotency_key() for p in partners]
    existing = list(Partner.objects.filter(idempotency_key__in=keys).values_list('idempotency_key', flat=True))
    new_items = [p for p in partners if p.idempotency_key() not in existing]
    addresses = update_address(new_items)
    partners = []
    for item in new_items:
        a = list(filter(lambda a: a.address==item.get_address(), addresses))[0]
        p = Partner(
        idempotency_key=item.idempotency_key(),
        data=asdict(item),
        address=a,
        received_at=parse_datetime(item.get_ts())
        )
        partners.append(p)
    
    return Partner.objects.bulk_create(partners)


def update_address(items: List[PartnerBase]) -> List[NormalizedAddress]:
    addresses = [item.get_address() for item in items]
    existing = NormalizedAddress.objects.filter(address__in=addresses).values_list('address')
    new_add = [add for add in addresses if add not in existing]
    NormalizedAddress.objects.bulk_create([
        NormalizedAddress(
            address=address
        )
        for address in new_add
    ])
    return list(NormalizedAddress.objects.filter(address__in=addresses))
