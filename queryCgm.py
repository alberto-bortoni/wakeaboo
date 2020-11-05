#! /usr/bin/python3

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
from pytz import timezone
import re
import config as cfg
import matrixDisplay as mat


#-------------------------------#
#             VARS              #
#*******************************#
printLog = True


#-------------------------------#
#         GET CGM DATA          #
#*******************************#
def queryCgmData():

  #-----get cloud info------#
  #cast date and correct for timezone bug
  rawImport  =  subprocess.check_output('wget -q -O - https://glucalarm.herokuapp.com/api/v1/entries/current/?token=raspi-97846cb04ad59b51 | head -n 1', shell=True)
  rawImport  = rawImport.decode('utf-8')
  castTab    = re.compile("[^\t]+")
  rawParts   = castTab.findall(rawImport)


  #-------error check-------#
  #TODO -- if cant parse, access tthen no data
  


  #-----print if enable-----#
  if cfg.printDebug:
    print(rawImport)

  if printLog:
    logFile  = open("logImport.txt", "a+")
    logFile.write(rawImport+"\n")
    logFile.close()


  #-----change timezone-----#
  #take timestamp
  #currently heroku reports only in 'z' or UTC time
  try:
    timeStr    = rawParts[0][1:20]

  except:
    if printLog:
      logFile  = open("logImport.txt", "a+")
      logFile.write("exception"+"\n")
      logFile.close()

  else:
    tmpTime    = datetime.strptime(timeStr, '%Y-%m-%dT%H:%M:%S')
    tmpTime    = tmpTime.replace(tzinfo = timezone('UTC'))
    cfg.bsTime = tmpTime.astimezone(timezone('US/Eastern'))


    #--------cast data--------#
    # if data is older than X min, no data
    if datetime.now(timezone('US/Eastern'))-timedelta(minutes=cfg.noDataTh) > cfg.bsTime:
      cfg.bsData = False
    else:
      cfg.bsData = True

    #cast bs
    tval        = rawParts[2]
    cfg.bsValue = int(tval,base = 10)

    #cast trend and drop
    cfg.bsTrend = rawParts[3][1:-1]

    if cfg.bsTrend == "DoubleUp":
      cfg.bsDirec = "up"
      cfg.bsDrop  = 2
    elif cfg.bsTrend == "SingleUp":
      cfg.bsDirec = "up"
      cfg.bsDrop  = 1
    elif cfg.bsTrend == "FortyFiveUp":
      cfg.bsDirec = "+45"
      cfg.bsDrop  = 0
    elif cfg.bsTrend == "Flat":
      cfg.bsDirec = "hor"
      cfg.bsDrop  = 0
    elif cfg.bsTrend == "FortyFiveDown":
      cfg.bsDirec = "-45"
      cfg.bsDrop  = 0
    elif cfg.bsTrend == "SingleDown":
      cfg.bsDirec = "dwn"
      cfg.bsDrop  = 1
    elif cfg.bsTrend == "DoubleDown":
      cfg.bsDirec = "dwn"
      cfg.bsDrop  = 2
    elif cfg.bsTrend == "nan":
      cfg.bsDirec = "nan"
      cfg.bsDrop  = 0
    else:
      cfg.bsDirec = "nan"
      cfg.bsDrop  = 0
#-----------------------------------------------#

#-------------------------------#
#          PRINT DATA           #
#*******************************#
def printCgmData():
  tswG = True
  tswT = True
  
  while True:
    tnow = datetime.now()

    if (tnow.hour>=22) or (tnow.hour<=10):
      if tswG:
        mat.clear8Mat()
        mat.clear16Mat()
        mat.dispGluc()
        time.sleep(10)
        mat.clear16Mat()
        tswG = False
        tswT = True
        
      queryCgmData()
      mat.dispBsArr()
      mat.printArrow()

    else:
      if tswT:
        mat.clear8Mat()
        mat.clear16Mat()
        mat.dispTim()
        time.sleep(10)
        mat.clear16Mat()
        tswG = True
        tswT = False

      mat.dispTime()

    time.sleep(60)    
#-----------------------------------------------#

#-------------------------------#
#          INIT FUNC            #
#*******************************#
#if excecuted as script
if __name__=='__main__':
  cfg.init()
  printCgmData()
#-----------------------------------------------#

#EOF#
