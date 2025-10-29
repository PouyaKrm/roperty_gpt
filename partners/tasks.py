from celery import shared_task

from partners.adapters import Normalizer
from partners.models import Partner

@shared_task
def insert_new():
    partners = Partner.objects.filter(normalized=False)[:10]
    data = []
    for p in partners:
        data.append(p.data)
    normalizer = Normalizer(data)
    