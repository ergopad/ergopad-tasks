import ccxt
import logging
import psycopg

from os import getenv
from time import mktime

# for xcg in ccxt.exchanges: ...
EXCHANGE_NAME = 'coinex'
SYMBOLS = ['ERG/USDT', 'ETH/USDT', 'BTC/USDT']
TIMEFRAMES = ['1m', '5m', '1d', '1w']
POSTGRES_CONN = getenv('POSTGRES_CONN')
LIMIT = 1000
DEBUG = True

# exchange = eval(f'ccxt.{exchangeName}()') # alternative using eval
exchange = getattr(ccxt, EXCHANGE_NAME)({
    'apiKey': getenv('COINEX_ACCESS_ID'), 
    'secret': getenv('COINEX_SECRET_KEY'),
})

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', level=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

def cleanupHistory():
    """
    Delete rows older than term
    """
    cleanupAfter = {
        '1m': '3 days',
        '5m': '3 weeks',
        '1d': '3 months',
        '1w': '3 years'
    }

    try:
        sqlResults = []
        with psycopg.connect(POSTGRES_CONN) as con:
            for symbol in SYMBOLS:
                logging.debug(f'symbol: {symbol}')
                for timeframe in TIMEFRAMES:
                    logging.debug(f'timeframe: {timeframe}')
                    cur = con.cursor()
                    tbl = f'{EXCHANGE_NAME}_{symbol}_{timeframe}'
                    logging.debug(f'tbl: {tbl}')
                    sqlCleanup = f"""delete from "{tbl}" where timestamp_utc < CURRENT_DATE - INTERVAL '{cleanupAfter[timeframe]}'"""
                    res = cur.execute(sqlCleanup)
                    if res.rowcount > 0:
                        logging.info(f'cleaned up {res.rowcount} rows in timeframe, {timeframe}...')
                        sqlResults.append({
                            'tbl': tbl,
                            'rows': res.rowcount
                        })
                    else:
                        sqlResults.append({                                
                            'tbl': tbl,
                            'rows': -1
                        })

        return {'status': 'success', 'message': sqlResults}

    except Exception as e:  # consider narrowing exception handing from generic, "Exception"
        logging.error(f'{myself()}: {e}')
        return {'status': 'error', 'message': e}

def putLatestOHLCV():
    try:
        sqlResults = []
        with psycopg.connect(POSTGRES_CONN) as con:
            for symbol in SYMBOLS:
                logging.debug(f'symbol: {symbol}')
                for timeframe in TIMEFRAMES:
                    logging.debug(f'timeframe: {timeframe}')
                    cur = con.cursor()
                    tbl = f'{EXCHANGE_NAME}_{symbol}_{timeframe}'
                    logging.debug(f'tbl: {tbl}')
                    since_dt = cur.execute(f"""select coalesce(max(timestamp_utc), '1/1/1900') as timestamp_utc from "{tbl}";""").fetchone()[0]
                    since = int(mktime(since_dt.timetuple()))
                    since_ms = since*1000
                    logging.debug(f'since: {since}/{since_dt}')
                    delLatest = cur.execute(f"""delete from "{tbl}" where timestamp_utc = '{since_dt}'""")
                    # ccxt implements exchange.has['fetchOHLCV'] to see if exchange has ohlcv ability
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=LIMIT)
                    ohlcv_dict = {}
                    ohlcv_dict = exchange.extend({}, exchange.indexBy(ohlcv, 0))
                    ohlcv_list = []
                    ohlcv_list = exchange.sort_by(ohlcv_dict.values(), 0)
                    candlesFrom = exchange.iso8601(ohlcv_list[0][0])
                    candlesTo = exchange.iso8601(ohlcv_list[-1][0])
                    for t_ms, o, h, l, c, v in ohlcv_list:
                        sql = f"""
                            insert into "{tbl}" (timestamp_utc, open, high, low, close, volume) 
                            values (timestamp 'epoch'+{int(t_ms/1000)}*INTERVAL '1 second', {o}, {h}, {l}, {c}, {v})
                            returning timestamp_utc
                        """
                        # logging.debug(f'sql: {sql}')
                        try: ins = cur.execute(sql).fetchone()[0]
                        except Exception as e: logging.error(f'ERR: {sql[0:100]}...; msg: {e}'); pass
                        sqlResults.append({
                            'tbl': tbl,
                            # 'ohlcv': [o, h, l, c, v],
                            # 'candles': f'from: {candlesFrom}, to: {candlesTo}',
                        })
                        # logging.debug(sql)

        return {'status': 'success', 'message': sqlResults}

    except Exception as e:
        logging.error(f'{myself()}: {e}')
        return {'status': 'error', 'message': e}

