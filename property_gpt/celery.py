# myproject/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'property_gpt.settings')
app = Celery('property_gpt')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-daily-report': {
        'task': 'partners.tasks.insert_new',
        'schedule': crontab(hour=8, minute=0),  # every day at 8:00 AM
        'args': (),
    },
}