from gevent import monkey,spawn,sleep, wait
monkey.patch_all()
from hyload.stats import Stats
from hyload.logger import TestLogger
from hyload.httpclient import HttpClient


__all__ = [
    'sleep', 'Stats', 'TestLogger', 'HttpClient',
    'run_task', 'wait_for_tasks_done'
]


_task_list =[]

def run_task(target, *args, **kwargs):
    global _task_list
    _task_list.append(spawn(target, *args, **kwargs))



def wait_for_tasks_done():
    global _task_list
    wait(_task_list)
    print('\n==== all tasks end ====\n')

def wait_for_ever():
    wait()

