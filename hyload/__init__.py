from gevent import monkey,spawn,sleep, wait
monkey.patch_all()
from .stats import Stats
from .logger import TestLogger
from .httpclient import HttpClient, create_ct_body_for_uploading


__all__ = [
    'sleep', 'Stats', 'TestLogger', 'HttpClient',
    'run_task', 'wait_for_tasks_done', 'create_ct_body_for_uploading'
]


_task_list =[]

def run_task(target, *args, **kwargs):
    global _task_list
    _task_list.append(spawn(target, *args, **kwargs))



def wait_for_tasks_done():
    global _task_list
    wait(_task_list)
    sleep(1.2) # wait for stats routine to send last second stats
    print('\n==== all tasks end ====\n')

def wait_for_ever():
    wait()

