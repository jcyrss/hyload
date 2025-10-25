import logging
import logging.handlers
import sys,os
from datetime import datetime
from .util import getCurTime


def getCommandArg(argName):
    for arg in sys.argv[1:]:
        if f'{argName}=' in arg:
            value = arg.replace(f'{argName}=','')
            return value
    
    return None

class Logger:
    
    
    loggerMap = {}
    
    @staticmethod 
    def getLogger(loggerName,toFile=True, toScreen=True, level=20):   
        if loggerName not in Logger.loggerMap.keys():   
            
            logger = logging.getLogger(loggerName)
            
            if os.name == 'posix':
                fileHdlr = logging.handlers.RotatingFileHandler(loggerName, maxBytes=1024*1024*15, backupCount=5000)
            else:
                fileHdlr = logging.FileHandler(loggerName)
            
            
            try:
                streamHdlr = logging.StreamHandler(strm=sys.stdout)
            except:
                streamHdlr = logging.StreamHandler(stream=sys.stdout)
            
            formatter = logging.Formatter("%(asctime)-15s ] %(message)s")
            
            fileHdlr.setFormatter(formatter)
            streamHdlr.setFormatter(formatter)
            
            if toFile:
                logger.addHandler(fileHdlr)
                
            if toScreen:
                logger.addHandler(streamHdlr)
            
            logger.setLevel(level)
            
            Logger.loggerMap[loggerName] = logger
            
            return logger
    
    
        else:
            return Logger.loggerMap[loggerName]
    
    

    @staticmethod 
    def setLogLevel(loggerName,level):
        logger = logging.getLogger(loggerName)   
        
        logger.setLevel(level)

class TestLogger:

    logFh  = None

    @classmethod
    def open_log(cls):
        dt = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

        logPath = getCommandArg('logPath')
        if logPath is None:
            logPath = './log'

        os.makedirs(logPath,exist_ok=True)
        logFile = os.path.join(logPath,f'{dt}.log')

        cls.logFh = open(logFile,'w',encoding='utf8',buffering=1) 
    
    @classmethod
    def write(cls,info:str):
        """write the parameter string into log file.

        Parameters
        ----------
        info : str
            the string to be written into log file.
        """
        if not cls.logFh:
            cls.open_log()
        
        cls.logFh.write(f'{getCurTime():.4f}|{info}\n')