import matplotlib.pyplot as plt
import json
import pprint,time
from datetime import datetime
import matplotlib.dates as md


# processStatsFiles
def ps(file,beginTime=None,endTime=None):
    print(beginTime);
    print(endTime);

    intBeginTime = 0
    intEndTime   = 9999999999
    tmfmt = '%Y-%m-%d %H:%M:%S'
    
    if beginTime:
        intBeginTime = int(time.mktime(time.strptime(beginTime, tmfmt)))
    
    if endTime:
        intEndTime = int(time.mktime(time.strptime(endTime, tmfmt)))


    names="time, cpu_usage,cpu_idle,cpu_user,cpu_nice,cpu_system,  memTotal,memused,mem_usage,buffers,cached,swapTotal,swapFree, avgqu_sz,await,util"

    print('read data...',end='')

    with open(file) as f:
        lines = f.read().splitlines()

    seconds = []
    cpu_usage = []
    mem_usage  = []
    io_await  = []

    for line in lines:
        if not line:
            continue
        
        parts = line.split(',')

        second = int(parts[0])
        if not  intBeginTime <= second <= intEndTime:
            continue

        seconds.append(datetime.fromtimestamp(second))
        cpu_usage.append(int(parts[1][:-3]))  # remove char '%'
        mem_usage.append(int(parts[7][:-3]))
        io_await.append(int(parts[14][:-2]))
        # io_avgqusz.append(parts[13])

    datenums = md.date2num(seconds)

    print('ok')
    
    print('ploting...',end='')


    # first subplot
    plt.subplot(3,1,1) 
    plt.title('')
    plt.ylabel('CPU Usage')
    # plt.axis([None, None, 0, 100])  # [xmin, xmax, ymin, ymax]
   
    xfmt = md.DateFormatter('%H:%M:%S')  #'%Y-%m-%d %H:%M:%S'
    plt.gca().xaxis.set_major_formatter(xfmt) 
    # plt.xticks(rotation=70)
    # plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.plot(datenums,cpu_usage, 'b-', linewidth=1)


    # first subplot
    plt.subplot(3,1,2) 
    plt.title('')
    plt.ylabel('Memory Usage')
    # plt.axis([None, None, 0, 100])  # [xmin, xmax, ymin, ymax]
    
    xfmt = md.DateFormatter('%H:%M:%S')  #'%Y-%m-%d %H:%M:%S'
    plt.gca().xaxis.set_major_formatter(xfmt)
    # plt.xticks(rotation=70)
    plt.plot(datenums,mem_usage, 'r-', linewidth=1)

    # second subplot
    plt.subplot(3,1,3)
    plt.title('')
    plt.ylabel('Disk Await')
    
    xfmt = md.DateFormatter('%H:%M:%S')  #'%Y-%m-%d %H:%M:%S'
    plt.gca().xaxis.set_major_formatter(xfmt)
    # plt.xticks(rotation=70)
    plt.plot(datenums,io_await, 'g-', linewidth=1)

    print('ok')
    

    plt.show()



