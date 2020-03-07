#! /usr/bin/python


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import os
import time
import subprocess
from subprocess import PIPE, STDOUT
import shlex
from time import sleep
import RPi.GPIO as GPIO
from random import *
from datetime import datetime
from datetime import timedelta
import re

# current BS state
rawImport = None # from nighscout
bsTime    = datetime.now()
bsValue   = 0  # mg/dl
bsTrend   = 0  # 1:90up 2:45up 3:flat 4:45down 5:90down
bsDrop    = 0  # 0:noSpeed 1:oneArrow 2:twoArrow
bsData    = False # 0:noData  1:data
noDataTh  = 10 # no data treshold in min
timeStr   = None

while True:

  #cast date and correct for timezone bug
  rawImport  =  subprocess.check_output(["wget","-q","-O","-","https://wakeaboo.herokuapp.com/api/v1/entries/current/?token=raspi-97846cb04ad59b51"])
  castTab    = re.compile("[^\t]+")
  rawParts   = castTab.findall(rawImport)

  #TODO -- if cant parse, access tthen no data
  #if bsData
  timeStr = rawParts[0][1:20]
  bsTime  = datetime.strptime(timeStr, '%Y-%m-%dT%H:%M:%S')
  bsTime  = bsTime - timedelta(hours=5) 

  # if data is older than X min, no data
  if datetime.now()-timedelta(minutes=noDataTh) > bsTime:
    bsData = False
  else:
    bsData = True

  #cast bs
  tval    = rawParts[2]
  bsValue = int(tval,base=10)

  #cast trend and drop
  trend = rawParts[3][1:-1]

  if trend == "DoubleUp":
    bsTrend = 1
    bsDrop  = 2
  elif trend == "SingleUp":
    bsTrend = 1
    bsDrop  = 1
  elif trend == "FortyFiveUp":
    bsTrend = 2
    bsDrop  = 0
  elif trend == "Flat":
    bsTrend = 3
    bsDrop  = 0
  elif trend == "FortyFiveDown":
    bsTrend = 4
    bsDrop  = 0
  elif trend == "SingleDown":
    bsTrend = 5
    bsDrop  = 1
  elif trend == "DoubleDown":
    bsTrend = 5
    bsDrop  = 2

  rawImport = None

  print "time {}".format(bsTime)
  print "data {}".format(bsData)
  print "value {}".format(bsValue)
  print "trendT {}".format(trend)
  print "trend {}".format(bsTrend)
  print "drop {}".format(bsDrop)
  time.sleep(5)    
