from celery import Celery
from celery.schedules import crontab

import celeryconfig
celery = Celery(__name__)
celery.config_from_object(celeryconfig)

# Schedules
# celery.conf.beat_schedule = {'every10s': {'task': 'tasks.hello', 'schedule': 10.0, 'args': (['world'])}}
celery.conf.beat_schedule = {

    # vesting
    'vesting_1d': {
        'task': 'redeem_ergopad',
        'schedule': crontab(hour=7, minute=10), # daily at 7:10
        # 'options': {'queue' : 'omega'}, # default
    },
    # 'vesting1m': {'task': 'redeem_ergopad', 'schedule': crontab(minute='*/1')},

    # scrape coin data
    'ergowatch_scrape_5m': {
        'task': 'scrape_price_data',
        'schedule': crontab(minute='*/5'), # every 5 mins
        # 'args': (['world'])
        # 'options': {'queue' : 'alpha'}, # default
    },

    'ergodex_scrape_5m': {
        'task': 'scrape_price_ergodex',
        'schedule': crontab(minute='*/5'), # every 5 mins
        # 'args': (['world'])
        # 'options': {'queue' : 'alpha'}, # default
    },

    # cleanup 5m price tables
    'cleanup_scrape_1d': {
        'task': 'cleanup_continuous_5m',
        'schedule': crontab(hour=6, minute=5), # daily at 6:05
    },

    'coinex_scrape_1m': {
        'task': 'coinex_scrape_all',
        'schedule': crontab(minute='*/1'), # every min
    },

    'coinex_cleanup_1d': {
        'task': 'coinex_cleanup_all',
        'schedule': crontab(hour=2, minute=25), # daily at 2:25
    },

}
