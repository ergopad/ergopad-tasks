import psycopg
import requests 

from celery import Celery
from os import getenv
from time import sleep, time
from ergodex import cleanupHistoricalErgodex, getErgodexToken

POSTGRES_CONN = getenv('POSTGRES_CONN')
ergo_watch_api: str = f'https://ergo.watch/api/sigmausd/state'
nerg2erg = 10**9

DEBUG = True

import celeryconfig
celery = Celery(__name__)
celery.config_from_object(celeryconfig)

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', level=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

class TaskFailure(Exception):
   pass

#region ROUTING
def backoff(attempts):
    return 2**attempts

@celery.task(name="create_task")
def create_task(task_type):
    sleep(int(task_type) * 10)
    return True 

@celery.task(name='redeem_ergopad', bind=True, default_retry_delay=300, max_retries=5)
def redeem_ergopad(self):
    try:
        res = requests.get('https://ergopad.io/api/vesting/redeem/Y2JDKcXN5zrz3NxpJqhGcJzgPRqQcmMhLqsX3TkkqMxQKK86Sh3hAZUuUweRZ97SLuCYLiB2duoEpYY2Zim3j5aJrDQcsvwyLG2ixLLzgMaWfBhTqxSbv1VgQQkVMKrA4Cx6AiyWJdeXSJA6UMmkGcxNCANbCw7dmrDS6KbnraTAJh6Qj6s9r56pWMeTXKWFxDQSnmB4oZ1o1y6eqyPgamRsoNuEjFBJtkTWKqYoF8FsvquvbzssZMpF6FhA1fkiH3n8oKpxARWRLjx2QwsL6W5hyydZ8VFK3SqYswFvRnCme5Ywi4GvhHeeukW4w1mhVx6sbAaJihWLHvsybRXLWToUXcqXfqYAGyVRJzD1rCeNa8kUb7KHRbzgynHCZR68Khi3G7urSunB9RPTp1EduL264YV5pmRLtoNnH9mf2hAkkmqwydi9LoULxrwsRvp', verify=False)
        if res.ok:
            return res.json()
        else:
            raise TaskFailure(f'redeem_ergopad: {res.text}')
            # return {'status': 'failed', 'message': res.text}

    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

@celery.task(bind=True, default_retry_delay=300, max_retries=5)
def hello(self, word: str) -> str:
    try:
        return {"Hello": word}
    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

@celery.task(name='scrape_price_data', acks_late=True, bind=True, default_retry_delay=300, max_retries=5)
def scrape_price_data(self):
    try:
        res = requests.get(ergo_watch_api).json()
        if res:
            sigUsdPrice = 1/(res['peg_rate_nano']/nerg2erg)
            circ_sigusd_cents = res['circ_sigusd']/100.0  # given in cents
            peg_rate_nano = res['peg_rate_nano']  # also SigUSD
            reserves = res['reserves']  # total amt in reserves (nanoerg)
            # lower of reserves or SigUSD*SigUSD_in_circulation
            liabilities = min(circ_sigusd_cents * peg_rate_nano, reserves)
            equity = reserves - liabilities  # find equity, at least 0
            if equity < 0:
                equity = 0
            if res['circ_sigrsv'] <= 1:
                sigRsvPrice = 0.0
            else:
                sigRsvPrice = equity/res['circ_sigrsv']/nerg2erg  # SigRSV
            with psycopg.connect(POSTGRES_CONN) as con:
                cur = con.cursor()
                sql = f"""
                    insert into "ergowatch_ERG/sigUSD/sigRSV_continuous_5m" (timestamp_utc, "sigUSD", "sigRSV") 
                    values (timestamp 'epoch'+{time()}*INTERVAL '1 second', {sigUsdPrice}, {sigRsvPrice})
                    returning timestamp_utc
                """
                ins = cur.execute(sql).fetchone()[0]
            return {'status': 'success', 'sql': sql, 'message (timestamp_utc)': ins}
        else:
            return {'status': 'failed', 'message': res.text}

    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

@celery.task(name='scrape_price_ergodex', acks_late=True, bind=True, default_retry_delay=300, max_retries=5)
def scrape_price_ergodex(self):
    try:
        res = getErgodexToken()
        if res:
            with psycopg.connect(POSTGRES_CONN) as con:
                cur = con.cursor()
                sql = f"""
                    insert into "ergodex_ERG/ergodexToken_continuous_5m" (timestamp_utc, sigusd, sigrsv, erdoge, lunadog, ergopad, neta) 
                    values (timestamp 'epoch'+{time()}*INTERVAL '1 second', {res['sigusd'][0]}, {res['sigrsv'][0]}, {res['erdoge'][0]}, {res['lunadog'][0]}, {res['ergopad'][0]}, {res['neta'][0]})
                    returning timestamp_utc
                """
                ins = cur.execute(sql).fetchone()[0]
            return {'status': 'success', 'sql': sql, 'message (timestamp_utc)': ins}
        else:
            return {'status': 'failed', 'message': res.text}
            
    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

@celery.task(name='cleanup_continuous_5m', acks_late=True, bind=True, default_retry_delay=300, max_retries=5)
def cleanup_continuous_5m(self):
    try:
        with psycopg.connect(POSTGRES_CONN) as con:
            cur = con.cursor()
            sql1 = f"""delete from "ergodex_ERG/ergodexToken_continuous_5m" where timestamp_utc < CURRENT_DATE - INTERVAL '5 years' returning timestamp_utc"""
            sql2 = f"""delete from "ergowatch_ERG/sigUSD/sigRSV_continuous_5m" where timestamp_utc < CURRENT_DATE - INTERVAL '5 years' returning timestamp_utc"""
            dlt1 = cur.execute(sql1).fetchone()[0]
            dlt2 = cur.execute(sql2).fetchone()[0]

            return {'status': 'success', 'sql': f'{sql1}\n{sql2}', 'message (timestamp_utc)': f'{dlt1}\n{dlt2}'}
            
    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
#endregion ROUTING
