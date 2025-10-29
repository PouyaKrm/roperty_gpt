from partners.adapters import Normalizer
from partners.models import Partner


def add_new_record(batch_data):
    normalizer = Normalizer(batch_data)
    kv = normalizer.get_idempotency_key_data()
    keys = [k for k, v in kv]
    existing = Partner.objects.filter(idempotency_key__in=keys).values_list('idempotency_key')
    new_items = [v for v in kv if v[0] not in existing]
    return Partner.objects.bulk_create(objs=[
        Partner(
        idempotency_key=new_items[0],
        data = new_items[1]
        )
    ])


