from partners.adapters import Normalizer
from partners.models import NormalizedAddress, Partner


def add_new_record(batch_data):
    normalizer = Normalizer(batch_data)
    kv = normalizer.get_idempotency_key_data()
    keys = [k for k, v in kv]
    existing = Partner.objects.filter(idempotency_key__in=keys).values_list('idempotency_key')
    new_items = [v for v in kv if v[0] not in existing]
    addresses = update_address(new_items)
    partners = []
    for item in addresses:
        a = list(filter(lambda a: a.address==item[2], addresses))[0]
        p = Partner(
        idempotency_key=item[0],
        data = item[1],
        address = a
        )
        partners.append(p)
    
    return Partner.objects.bulk_create(partners)


def update_address(kv) -> list[NormalizedAddress]:
    addresses = [v[2] for v in kv]
    existing = NormalizedAddress.objects.filter(address__in=addresses).values_list('address')
    new_add = [add for add in addresses if add not in existing]
    NormalizedAddress.objects.bulk_create([
        NormalizedAddress(
            address=address
        )
        for address in new_add
    ])
    return list(NormalizedAddress.objects.filter(address__in=addresses))
