# %%
import utcnow
import psycopg2
# import requests
import asyncio, aiohttp  # pip install aiohttp aiodns

from os import getenv
from discord import Webhook, RequestsWebhookAdapter
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select, delete
from datetime import datetime

# %%
import logging
# logging.basicConfig(format='{asctime}:{name:>8s}:{level:<8s}::{message}', style='{', level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

import inspect
myself = lambda: inspect.stack()[1][3]

# %%
from sqlmodel.sql.expression import Select, SelectOfScalar

SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore

# %%
ERGOPAD_DISCORD_WEBHOOK = getenv('ERGOPAD_DISCORD_WEBHOOK')
DATABASE = getenv('DATABASE')
eng = create_engine(DATABASE)

# %%
class ErgoBeans(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    url: str
    type: str
    recent_height: Optional[int] = Field(default=-1)

class BeanCounter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ergobean_id: int
    ergo_height: int = Field(default=-1)
    bean_height: int = Field(default=-1)
    counted_at: datetime = Field(default_factory=utcnow(), nullable=False)

# %%
def cleanup_db():
    with Session(eng) as session:
        res = session.exec(delete(BeanCounter))
        res = session.exec(delete(ErgoBeans))
        session.commit()
        logging.debug(f'rowcount: {res.rowcount}')

# cleanup_db()

# %%
def create_db_and_tables():
    SQLModel.metadata.create_all(eng)

# create_db_and_tables()

# %%
def create_beans():
    beans = {
        'alpha': ErgoBeans(name='alpha node', url='http://54.214.59.165:9053/info', type='ergonode'),
        'beta': ErgoBeans(name='beta node', url='http://52.12.102.149:9053/info', type='ergonode'),
        'winter': ErgoBeans(name='winter node', url='http://node:9053/info', type='ergonode'),
        'alpha_xpl': ErgoBeans(name='alpha explorer', url='http://54.214.59.165:9090/api/v1/networkState', type='explorer'),
        'beta_xpl': ErgoBeans(name='beta explorer', url='http://52.12.102.149:9090/api/v1/networkState', type='explorer'),
        'public_xpl': ErgoBeans(name='public explorer', url='http://api.ergoplatform.com/api/v1/networkState', type='explorer'),
    }

    session = Session(eng)
    for b in beans:
        # print(beans[b])
        session.add(beans[b])
    session.commit()

# create_beans()

# %%
def get_beans():
    beans = None
    with Session(eng) as session:
        sql = select(ErgoBeans)
        beans = session.exec(sql).all()
        [logging.debug(b) for b in beans]
        
    return beans

# %%
def alertAdmin(subject, body):
    return {} 
    
    try:
        webhook = Webhook.from_url(ERGOPAD_DISCORD_WEBHOOK, adapter=RequestsWebhookAdapter())       
        webhook.send(content=f':bangbang:HEIGHT_VALIDATOR:bangbang:\nsubject: `{subject}`\nbody: `{body}`')

    except Exception as e:
        logging.error(f'ERR:{myself()}: cannot display discord msg ({e})')

alertAdmin('begin height validator', utcnow())

# %%
# Find height of node/explorer
async def getHeight(
    session: aiohttp.ClientSession,
    bean: ErgoBeans,
    **kwargs
) -> dict:
    try:
        resp = await session.request('GET', url=bean.url, **kwargs)
        data = await resp.json()
        
        if bean.type == 'ergonode': 
            return {
                'id': bean.id,
                'name': bean.name,
                'height': int(data['fullHeight'])
            }

        if bean.type == 'explorer': 
            return {
                'id': bean.id,
                'name': bean.name,
                'height': int(data['height'])
            }

    except:
        return {
            'url': bean.url,
            'height': -1
        }

### MAIN
async def height(beans, **kwargs):
    try:
        async with aiohttp.ClientSession() as aio:
            
            # build async call
            tasks = []
            for b in beans: 
                tasks.append(getHeight(aio, b))
            
            # simultaneous request all heights
            res = await asyncio.gather(*tasks, return_exceptions=True)

            # find current maximum from all sources
            cur = max([ht['height'] for ht in res])
            logging.info(f'current height: {cur}')

            # results; alert/log if more than 2 height difference
            now = utcnow()
            issues = []
            session = Session(eng)
            for r in res:
                if cur - r['height'] < 3:
                    logging.debug(f'''{r['name']}: {r['height']}''')
                    # session.add(BeanCounter(ergobean_id=r['id'],  ergo_height=r['height'], bean_height=r['height'], counted_at=now)) # testing
                else:
                    # record issues
                    logging.error(f'''{r['name']}: {r['height']} behind by {cur-r['height']}''')
                    issues.append(f'''node {r['name']} at height {r['height']}, should be {cur}; {now}''')
                    session.add(BeanCounter(ergobean_id=r['id'],  ergo_height=r['height'], bean_height=r['height'], counted_at=now))
            session.commit()
            
            if not issues == []:
                alertAdmin('height issue', f'ISSUES:\n{chr(10).join([i for i in issues])}')

        return {'status': 'success'}

    except Exception as e:
        return {'status': e}

if __name__ == '__main__':
    beans = get_beans()
    asyncio.run(height(beans))
