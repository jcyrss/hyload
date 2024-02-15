import sys
import time

def _gct37():
    return time.time_ns() / (10 ** 9)

def _gct36():
    return time.time()


if sys.version_info >= (3, 7):
    getCurTime = _gct37
else:
    getCurTime = _gct36



def high_process_priority():
    """ Set the priority of the process to below-normal."""

    try:
        sys.getwindowsversion()
    except AttributeError:
        isWindows = False
    else:
        isWindows = True

    if isWindows:
        # Based on:
        #   "Recipe 496767: Set Process Priority In Windows" on ActiveState
        #   http://code.activestate.com/recipes/496767/
        import win32api,win32process,win32con

        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        print('set to HIGH_PRIORITY_CLASS')
        win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)
    else:
        import os

        os.nice(1)