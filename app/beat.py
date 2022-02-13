from celery import Celery
from celery.schedules import crontab

import celeryconfig
celery = Celery(__name__)
celery.config_from_object(celeryconfig)

# Schedules
# celery.conf.beat_schedule = {'every10s': {'task': 'tasks.hello', 'schedule': 10.0, 'args': (['world'])}}
celery.conf.beat_schedule = {

    # vesting
    'vesting1d': {
        'task': 'redeem_ergopad',
        'schedule': crontab(hour=7), # daily at 7a UTC
        # 'options': {'queue' : 'omega'}, # default
    },
    # 'vesting1m': {'task': 'redeem_ergopad', 'schedule': crontab(minute='*/1')},

    # scrape coin data
    'scrape5m': {
        'task': 'scrape_price_data',
        'schedule': crontab(minute='*/5'), # every 5 mins
        # 'args': (['world'])
        # 'options': {'queue' : 'alpha'}, # default
    },

}
