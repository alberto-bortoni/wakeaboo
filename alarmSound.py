#! /usr/bin/python

#################################
#             HEAD              #
#################################
#########import mplayer
import os
import time
import subprocess
from subprocess import PIPE, STDOUT
import shlex
from time import sleep
from random import *
import config as cfg


#################################
#       VOLUME CONTROLS         #
#################################

# increases volume by sending a character command to mplayer
# 0 is mplayer's command to increase
def increase_volume():
  if (cfg.alarmVol < cfg.alarmVolMax):
    cfg.alarmVol = cfg.alarmVol + cfg.alarmVolSt
    player.stdin.write('0')
    player.stdin.flush()

# decreases volume by sending a character command to mplayer
# 9 is mplayer's command to decrease
def decrease_volume():
  if (cfg.alarmVol > cfg.alarmVolMin):
    cfg.alarmVol = cfg.alarmVol - cfg.alarmVolSt
    player.stdin.write('9')
    player.stdin.flush()

#################################
#             MAIN              #
#################################

def soundAlarm():
  #try:
  #  cfg.alarm.terminate()

  tmp = cfg.errorAlarmFile

  if(cfg.noData):
    tmp = cfg.errorAlarmFile
  elif(cfg.bsHighLatch):
    tmp = cfg.highAlarmFile
  elif(cfg.bsUrLowLatch):
    tmp = cfg.urLowAlarmFile
  elif(cfg.bsLowLatch):
    tmp = cfg.lowAlarmFile
  elif(cfg.bsDropLatch):
    tmp = cfg.dropAlarmFile

  cfg.alarm = subprocess.Popen(["mplayer", "-volume", str(cfg.alarmVol), "-really-quiet", tmp], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
  time.sleep(2)
#-----------------------------------------------#

def alarmServ():
  if (time.time()-cfg.alarmTimLast >= cfg.alarmIncTim):
    cfg.alarmTimLast = time.time()
    increase_volume()
#-----------------------------------------------#

def killa():
  cfg.alarmVol = cfg.alarmVol+1  
#-----------------------------------------------#

def killAlarm():
  print(highAlarmFile)  
  print(cfg.alarmVol)
  #cfg.alarm.terminate()
#-----------------------------------------------#

#EOF#
