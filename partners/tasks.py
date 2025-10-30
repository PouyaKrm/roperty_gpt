from celery import shared_task

from partners.models import Listing, NormalizedAddress, Partner, to_partner_data_class_from_data
from django.db import transaction

from partners.services import get_partners, insert_new_listing_from_partner, mark_partner_as_normaized

@shared_task
def insert_listing():
    partners = get_partners()
    insert_new_listing_from_partner(partners)
    