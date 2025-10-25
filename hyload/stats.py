from .util import getCurTime
import time,sys,json,socket,os,gevent
import http.client
from urllib.parse import quote_plus
from .logger import TestLogger
from typing import Union,List
from datetime import datetime
from random import randint

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def getCommandArg(argName):
    for arg in sys.argv[1:]:
        if f'{argName}=' in arg:
            value = arg.replace(f'{argName}=','')
            return value
    
    return None

# 控制台程序地址
ConsoleAddr = getCommandArg('console')
if ConsoleAddr:
    # print (f'Console addr:{ConsoleAddr}')
    # consoleConnection = http.client.HTTPConnection(
    #                             ConsoleAddr,  #ConsoleAddr 'httpbin.org'
    #                             timeout=0.3)

    # Create a UDP socket at client side

    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    parts = ConsoleAddr.split(':')
    UDPServerAddr = parts[0],int(parts[1])
    # print(UDPServerAddr)




class Stats:
    foStats = None
    responseTimeRanges = [100, 500, 1000,3000]
    
    # obsolete
    @staticmethod
    def wait_for_tasks_done(tasks:list=None):
        gevent.wait(tasks) # wait for tasks end
        time.sleep(1) # wait for stats routine to send last second stats
        print('\n==== tasks done ====')

    @classmethod
    def clear(cls):
        cls.startTime = getCurTime()

        cls.connectionNumber = 0 # not used currently

        # overall stats
        cls.totalSend = 0
        cls.totalRecv = 0
        cls.totalTimeout = 0
        cls.totalError = 0

        # stats of the second
        cls.rpsTable = {}
        cls.tpsTable = {}
        cls.responseTimeTable = {}
        cls.timeoutTable = {}
        cls.errorTable = {}    

        # count numbers per response time range 
        cls.responseTimeRangeTable =  { rtrn: 0 for rtrn in cls.responseTimeRanges}
        cls.responseTimeRangeTable[-1] = 0 # -1 reprents ulimited big
        # create responseTimeRangeTable with meaning like this:
        # {
        #     '0-100ms':     0,
        #     '100-500ms':   0,
        #     '500-1000ms':  0,
        #     '1000-3000ms': 0,
        #     '>=3000ms':    0,
        # } 
        
        cls.rangeToName =  {}
        for idx, rtrn in enumerate(cls.responseTimeRanges):
            if idx == 0:
                cls.rangeToName[rtrn] = f'0-{rtrn}ms'
            else:
                cls.rangeToName[rtrn] = f'{cls.responseTimeRanges[idx-1]}-{rtrn}ms'
        cls.rangeToName[-1] = f'>={rtrn}ms'
        
        cls.runFlag = False

        cls.logFh = None


    @classmethod
    def _sendStatsToConsoleTcp(cls, stats):
        if not ConsoleAddr:
            return
            
        consoleConnection = http.client.HTTPConnection(
                            ConsoleAddr,  #ConsoleAddr 'httpbin.org'
                            timeout=5)

        # print('send request to console----------')
        try:
            consoleConnection.request('GET', 
                     '/stats?value=' + quote_plus(json.dumps(stats)), 
                     
                    #  '/get?'+ quote_plus(json.dumps(stats).encode()), 
                     body=None,
                     headers={
                            'User-Agent' : "BYLOAD TESTER"
                        })                
            
            httpResponse = consoleConnection.getresponse()
            
            httpResponse.close()

        except Exception as e:
            print(f'send stats to console failed! {e}')


    @classmethod
    def _sendStatsToConsoleUdp(cls, statsBytes):
        if not ConsoleAddr:
            return
                       
        
        # print('send request to console----------')
        try:
            UDPClientSocket.sendto(
                statsBytes,
                UDPServerAddr)                
                            

        except Exception as e:
            print(f'send stats to console failed! {e}')


    @classmethod
    def _statsOneTable(cls,
                       strLastSecond,
                      lastSecond,
                      table,
                      tableName,
                      action,
                      statsOneSecond):

        if lastSecond in table:
            if cls.runFlag:
                print(f'{strLastSecond} {action} {table[lastSecond]:6}')
            statsOneSecond[tableName] = table[lastSecond]
            table.pop(lastSecond)
        else:
            statsOneSecond[tableName] = 0

    @classmethod
    def _one_second_data_done_stats(cls,lastSecond):
        """
        Finally, the data send to stats server is like this:
        
        {
            "t": 1594287838, 
            "rps": 100, 
            "tps": 100, 
            "respTimeSum": 0.0475, 
            "total": {
                "send": 1800, "recv": 1800, "0-100ms": 1795, "100-500ms": 5
            }   
        }
        """
        strLastSecond = time.strftime('%H:%M:%S',time.localtime(lastSecond))
         
        if (lastSecond not in cls.rpsTable) and \
            (lastSecond not in cls.tpsTable) and \
            (lastSecond not in cls.timeoutTable) and \
            (lastSecond not in cls.errorTable):     
            return   


        statsOneSecond = {'t':lastSecond}

        # rps
        cls._statsOneTable(strLastSecond,lastSecond,cls.rpsTable,'rps','send',statsOneSecond)

        # tops
        cls._statsOneTable(strLastSecond,lastSecond,cls.timeoutTable,'tops','timeout',statsOneSecond)

        # eps
        cls._statsOneTable(strLastSecond,lastSecond,cls.errorTable, 'eps','error',statsOneSecond)

        # tps、respTimeSum 、 avgRespTime
        if lastSecond in cls.tpsTable:
            count = cls.tpsTable[lastSecond]
            avgRespTime = cls.responseTimeTable[lastSecond]/count  
            if cls.runFlag:
                print(f'{strLastSecond} recv {count:6} | avg lantency {avgRespTime:.4f}')

            statsOneSecond['tps'] = count
            statsOneSecond['respTimeSum'] = round(cls.responseTimeTable[lastSecond],4)
            statsOneSecond['avgRespTime'] = round(avgRespTime,4)

            cls.tpsTable.pop(lastSecond)
            cls.responseTimeTable.pop(lastSecond)
        else:
            statsOneSecond['tps'] = 0
            statsOneSecond['respTimeSum'] = 0
            statsOneSecond['avgRespTime'] = 0


        if len(statsOneSecond) == 1:
            return

        total = {}
        total['send'] = cls.totalSend
        total['recv'] = cls.totalRecv

        if  cls.totalTimeout > 0 :
            total['timeout'] = cls.totalTimeout
        if  cls.totalError > 0 :
            total['error'] = cls.totalError

        # print(cls.responseTimeRangeTable)
        respTimeRanges = { cls.rangeToName[tr] : count  for tr,count in  cls.responseTimeRangeTable.items() if count>0}  
        # print(respTimeRanges) 
        total.update(respTimeRanges)

        statsOneSecond['total'] = total
                
        statsBytes = json.dumps(statsOneSecond).encode()

        if ConsoleAddr:
            cls._sendStatsToConsoleUdp(statsBytes)

        if cls.foStats:
            cls.foStats.write(statsBytes+b'\n')
            cls.foStats.flush()

        # stats of concurrent connection numbers 
        # It's difficult to detect connection broken, forget it for time being
        # cls._sendStatsToConsoleUdp({'connNum':cls.connectionNumber})

    @classmethod
    def start(cls):
        """
        Run stats routine.
        """

        statsfile = getCommandArg('statsfile')
        if not statsfile:  
            statsfile = os.path.join(
                'stats_perf', 
                datetime.now().strftime('%Y-%m-%d_%H.%M.%S.%f')[:23].replace("-0", "-") + '.sts')
        
        statsDir = os.path.dirname(statsfile)
        if statsDir:
            os.makedirs(statsDir,exist_ok=True)
        cls.foStats = open(statsfile,'wb')

        cls.clear()
        cls.runFlag = True 

        gevent.spawn(cls._independent_check)

                
    @classmethod
    def _independent_check(cls):

        # The current second it not over, 
        # So we just need to send stats of the last second.
        while True:

            if not cls.runFlag:
                break

            # check every 0.4 seconds
            time.sleep(0.4)

            curTime = getCurTime()

            # get last second to measure
            lastSecond = int(curTime) - 1

            cls._one_second_data_done_stats(lastSecond)


    @classmethod
    def stop(cls):
        """
        Stop stats routine.
        """
        # wait for more than 1 second, so stats greenlet could count last second
        time.sleep(1.5)
        cls.runFlag = False

        if cls.foStats:
            cls.foStats.close()
            cls.foStats = None

    @classmethod
    def _measure_per_second(cls, recTable, addAmount, curTime=None):
        
        if curTime is None:
            curTime = getCurTime()

        # get cur second to measure
        curSecond = int(curTime)
        # new second to stats
        if curSecond not in recTable:          
            recTable[curSecond] = addAmount            
            cls._one_second_data_done_stats(curSecond-1)
        # add one to  stats
        else:
            recTable[curSecond] += addAmount
        
        return curTime


    @classmethod
    def connection_num_increace(cls):
        cls.connectionNumber +=1

    @classmethod
    def connection_num_decreace(cls):
        cls.connectionNumber -=1


    @classmethod
    def one_sent(cls):

        sentTime = cls._measure_per_second(cls.rpsTable,1)
        cls.totalSend +=1

        return sentTime

        
    @classmethod
    def one_recv(cls,sentTime):
                
        recvTime = cls._measure_per_second(cls.tpsTable,1)
        cls.totalRecv +=1

        duration = recvTime - sentTime
        cls._measure_per_second(cls.responseTimeTable,duration,recvTime)

        durationInMs = duration*1000
        for rtrn in cls.responseTimeRanges:
            if durationInMs < rtrn:
                cls.responseTimeRangeTable[rtrn] +=1
                break
        else: # bigger than the last time range number
            cls.responseTimeRangeTable[-1] += 1 

        return recvTime

    @classmethod
    def one_timeout(cls):

        cls._measure_per_second(cls.timeoutTable, 1)
        cls.totalTimeout += 1

        return


    @classmethod
    def one_error(cls, log_info: Union[None,str] = None):
        """
        Add one error to the statistics result, and write the error info to log file if needed.

        Parameters
        ----------
        log_info : Union[None,str], optional
            (Optional) the error info to be written to log file.
        """

        cls._measure_per_second(cls.errorTable, 1)
        cls.totalError += 1

        if log_info:
            TestLogger.write(log_info)
        return
    
    @classmethod
    def set_response_time_ranges(cls, response_time_ranges:List[int]):
        """
        Set response time ranges so in the statistics we could see how many reponses in what response time range,
        like this

        0-100ms      : 100
        100-500ms    : 130
        500-1000ms   : 23
        >1000ms      : 3

        It should be called before calling the method `start`.

        Parameters
        ----------
        response_time_ranges : List[int]
            reponse time ranges, like [100, 500, 1000] will create the follwing ranges:            
            0-100ms , 100-500ms, 500-1000ms , >1000ms 

            if not set, [100, 500, 1000,3000] will be the default one.

        """
        
        cls.responseTimeRanges = response_time_ranges

Stats.clear()