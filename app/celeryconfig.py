from os import getenv
from kombu import Queue, Exchange

REDIS_HOST = getenv('REDIS_HOST')
REDIS_PORT = getenv('REDIS_PORT')

"""
=========
Notes:
=========
CPU Bound task
celery -A <task> worker -l info -n <name of task> -c 4 -Ofair -Q <queue name> — without-gossip — without-mingle — without-heartbeat

I/O task
celery -A <task> worker -l info -n <name of task> -Ofair -Q <queue name> -P eventlet -c 1000 — without-gossip — without-mingle — without-heartbeat
"""

broker_url = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
result_backend = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
result_exchange = 'default'
task_track_started = True
task_ignore_result = False # allows flower to check results
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['application/json', 'json', 'yaml']
timezone = 'UTC'
worker_send_task_event = False
task_time_limit = 300 # task will be killed after 5 mins
task_soft_time_limit = 180 # task will raise exception SoftTimeLimitExceeded after 3 mins
task_acks_late = True # task messages will be acknowledged after the task has been executed, not just before (the default behavior).
worker_prefetch_multiplier = 10 # One worker taks 10 tasks from queue at a time and will increase the performance

# exchanges
# default_exchange = Exchange('default', type='direct')
# media_exchange = Exchange('media', type='direct')

# queue
task_default_queue = 'default'
task_default_routing_key = 'default'
task_queue_max_priority = 10
task_default_priority = 5
# broker_transport_options = {'queue_order_strategy': 'priority',} # used for redis priority; may not be ideal
# task_queues = (
#     Queue('default',     routing_key='default'), # Queue('default', default_exchange, routing_key='task.#'),
#     Queue('alpha_tasks', routing_key='alpha.#', queue_arguments={'x-max-priority': 10}),
#     Queue('omega_tasks', routing_key='omega.#', queue_arguments={'x-max-priority': 1}),
# )
# https://docs.celeryproject.org/en/stable/userguide/routing.html
task_routes = {
    'alpha.*': {
        'queue': 'alpha_tasks',
        'routing_key': 'alpha',
    },
    'omega.*': {
        'queue': 'omega_tasks',
        'routing_key': 'omega',
    },
}
# task_default_exchange_type = 'default'
task_default_exchange_type = 'direct'
