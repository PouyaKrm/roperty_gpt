from dataclasses import asdict
from gettext import translation
from typing import List
from partners.adapters import compute_dedupe_id
from partners.models import Listing, NormalizedAddress, Partner, PartnerBase, to_partner_data_class_from_data, to_partner_list_data_class_from_data
from django.utils.dateparse import parse_datetime
from django.utils import timezone

def add_new_record(batch_data):
    partners = to_partner_list_data_class_from_data(batch_data)
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
        received_at=parse_datetime(item.get_ts()),
        lat=item.get_lat(),
        lon=item.get_lon(),
        dedupe_key=compute_dedupe_id(item.get_address(), item.get_lat(), item.get_lon())
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

def get_partners():
        partners = Partner.objects.filter(normalized=False).all()[:10]
        ids = []
        result = []
        for p in partners:
            if p.dedupe_key not in ids:
                result.append(p)
                ids.append(p.dedupe_key)
        return result

def mark_partner_as_normaized(dedupe_keys):
        Partner.objects.filter(dedupe_key__in=dedupe_keys, received_at__lt=timezone.now()).update(normalized=True)

def insert_new_listing_from_partner(partners):
        partners_data_class = [to_partner_data_class_from_data(p.data) for p in partners]
        dedup_ids = [p.get_dedupe_id() for p in partners_data_class]
        existing = Listing.objects.filter(dedupe_id__in=dedup_ids)
        with translation.atomic():
            _save_new(existing, partners_data_class)
            _update_existing(existing, partners_data_class)
            mark_partner_as_normaized(dedup_ids)


def _save_new(listing, partners_data_class):
    existing_id = [e.dedupe_id for e in listing]
    
    for p in partners_data_class:
        if p.get_dedupe_id() not in existing_id:
            listing = p.to_listing()
            address = NormalizedAddress.objects.filter(address=p.get_address()).first()
            listing.address = address
            listing.save()


def _update_existing(listging, partners_data_class):
    lookup = {o.get_dedupe_id(): o for o in partners_data_class}
    zipped = [(i, lookup[i.get_dedupe_id]) for i in listging if i.get_dedupe_id in lookup]   
    for l, p in zipped:
        changed = l.address.address != p.p.get_address() or l.lat != p.lat or l.lng != p.ln or l.price != p.price or l.beds != p.beds or l.baths != p.baths or l.status != p.status
        new_listing = p.to_listing()
        address = NormalizedAddress.objects.filter(address=p.get_address()).first()
        new_listing.address = address
        new_listing.id = l,id
        l.version = l.version + 1 if changed else l.version
        l.save()
        