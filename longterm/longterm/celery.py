from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'longterm.settings')

app = Celery('longterm')
app.config_from_object('django.conf:settings', namespace='CELERY')


app.conf.beat_schedule = {
    'scrape us stocks': {
        'task': 'api.tasks.scrape_us_stocks',
        'schedule': crontab(day_of_week='mon,tue,wed,thu,fri',
                            hour='17-0',
                            minute='0'
                            ),
        'options': {'queue': 'scraper'},
    },
    'scrape israeli stocks': {
        'task': 'api.tasks.scrape_isr_stocks',
        'schedule': crontab(day_of_week='sun,mon,tue,wed,thu',
                            hour='10-17',
                            minute='0'
                            ),
        'options': {'queue': 'scraper'},
    },
    # updates portfolio every day, every hour between 10:00 - 00:00
    'update portfolios': {
        'task': 'api.tasks.update_portfolios',
        'schedule': crontab(day_of_week='sun,mon,tue,wed,thu,fri,sat',
                            hour='10-0',
                            minute='0'
                            ),
        'options': {'queue': 'scraper'},
    },
}


app.autodiscover_tasks()