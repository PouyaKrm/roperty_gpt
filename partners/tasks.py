from celery import shared_task

from partners.models import Partner

@shared_task
def insert_new():
    Partner.objects.filter(normalized=False).lime