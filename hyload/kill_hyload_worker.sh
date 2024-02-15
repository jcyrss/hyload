#!/bin/sh

PROC_NAME=hyloadtest

ps -ef|grep $PROC_NAME|grep -v grep

SERVER_PROC_PID=`ps -ef | grep $PROC_NAME|grep -v grep |awk '{printf "%s ", $2}'`
for PID in $SERVER_PROC_PID
do
  if kill -9 $PID
     then
        echo "Process $PROC_NAME($PID) was stopped at " `date`
     else
        echo "Process $PROC_NAME($PID) can not be stopped at " `date`
   fi
done
