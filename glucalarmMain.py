#!/usr/bin/python3 -u

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
import config as cfg
#import initPiState
import matrixDisplay as mat
import sys
import queryCgm as cgm

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                             STARTUP STUFF                             #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                                TIMERS                                 #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

def timerServices():
  timer90Loop()
  timer15Loop()

#-------------------------------#
#         90MIN TIMER           #
#*******************************#
def initTimer90():
  cfg.tim90First  = False
  cfg.tim90Run    = False
  cfg.tim90Finish = False
  cfg.tim90End    = False
  cfg.tim90BtT0   = time.time()
  cfg.tim90Start  = time.time()
  cfg.tim90Last   = time.time()
#-----------------------------------------------#

def startTimer90():
  print('start 90min timer')
  cfg.tim90First  = False
  cfg.tim90Run    = True
  cfg.tim90Finish = False
  cfg.tim90End    = False
  cfg.tim90BtT0   = time.time()
  cfg.tim90Start  = time.time()
  cfg.tim90Last   = time.time()
  mat.fill16Bar(1)
  time.sleep(0.5)
  mat.fill16Bar(0)
  time.sleep(0.5)
#-----------------------------------------------#

def stopTimer90():
  print('stoping 90min timer')
  cfg.tim90First  = False
  cfg.tim90Run    = False
  cfg.tim90Finish = False
  cfg.tim90End    = False
  mat.fill16Bar(1)
  time.sleep(0.5)
  mat.fill16Bar(0)
  time.sleep(0.5)
  mat.fill16Bar(1)
  time.sleep(0.5)
  mat.fill16Bar(0)
#-----------------------------------------------#

def timer90Loop():
  if not (cfg.tim15First and cfg.tim15Run and cfg.tim15Finish and cfg.tim15End):
    if cfg.tim90First:
      startTimer90()

    elif cfg.tim90Run:
      if cfg.tim90Dur<=(time.time()-cfg.tim90Start):
        cfg.tim90Finish = True
      elif (time.time()-cfg.tim90Last)>0.5:
        cfg.tim90Last = time.time()
        mat.print16Bar(cfg.tim90Dur, (time.time()-cfg.tim90Start)) 

    elif cfg.tim90Finish:
      timer90Alarm()  

    elif cfg.tim90End:
      stopTimer90()
#-----------------------------------------------#

def timer90Alarm():
  #TODO -- add alarm
  if cfg.tim90Finish:
    stopTimer90()
    print('90 alarm')
    time.sleep(2)
    print('90 alarm off')
#-----------------------------------------------#

def timer90min_callback(chan):
  if not GPIO.input(cfg.pinTimerBt1) and not cfg.tim90BtPress:
    print('90minBt press', flush=True)
    cfg.tim90BtPress = True
    cfg.tim90BtT0    = time.time()
  elif cfg.tim90BtPress:
    print('90minBt depress', flush=True)
    cfg.tim90BtPress = False
    td = time.time()-cfg.tim90BtT0
    if td>2 and not cfg.tim90Run:
      cfg.tim90First = True
    elif td>2 and cfg.tim90Run:
      cfg.tim90End   = True
  else:
    cfg.tim90BtPress = False
#-----------------------------------------------#

#-------------------------------#
#         15MIN TIMER           #
#*******************************#
def initTimer15():
  cfg.tim15First  = False
  cfg.tim15Run    = False
  cfg.tim15Finish = False
  cfg.tim15End    = False
  cfg.tim15BtT0   = time.time()
  cfg.tim15Start  = time.time()
  cfg.tim15Last   = time.time()
#-----------------------------------------------#

def startTimer15():
  print('start 15min timer')
  cfg.tim15First  = False
  cfg.tim15Run    = True
  cfg.tim15Finish = False
  cfg.tim15End    = False
  cfg.tim15BtT0   = time.time()
  cfg.tim15Start  = time.time()
  cfg.tim15Last   = time.time()
  mat.fill16Bar(1)
  time.sleep(0.5)
  mat.fill16Bar(0)
  time.sleep(0.5)
#-----------------------------------------------#

def stopTimer15():
  print('stoping 15min timer')
  cfg.tim15First  = False
  cfg.tim15Run    = False
  cfg.tim15Finish = False
  cfg.tim15End    = False
  mat.fill16Bar(1)
  time.sleep(0.5)
  mat.fill16Bar(0)
  time.sleep(0.5)
  mat.fill16Bar(1)
  time.sleep(0.5)
  mat.fill16Bar(0)
#-----------------------------------------------#

def timer15Loop():
  if not (cfg.tim90First and cfg.tim90Run and cfg.tim90Finish and cfg.tim90End):
    if cfg.tim15First:
      startTimer15()

    elif cfg.tim15Run:
      if cfg.tim15Dur<=(time.time()-cfg.tim15Start):
        cfg.tim15Finish = True
      elif (time.time()-cfg.tim15Last)>0.5:
        cfg.tim15Last = time.time()
        mat.print16Bar(cfg.tim15Dur, (time.time()-cfg.tim15Start)) 

    elif cfg.tim15Finish:
      timer15Alarm()

    elif cfg.tim15End:
      stopTimer15()
#-----------------------------------------------#

def timer15Alarm():
  #TODO -- add alarm
  if cfg.tim15Finish:
    stopTimer15()
    print('15 alarm')
    time.sleep(2)
    print('15 alarm off')
#-----------------------------------------------#

def timer15min_callback(chan):
  if not GPIO.input(cfg.pinTimerBt2) and not cfg.tim15BtPress:
    print('15minBt press', flush=True)
    cfg.tim15BtPress = True
    cfg.tim15BtT0    = time.time()
  #elif GPIO.input(cfg.pinPowerBt) and cfg.pwrBtPress:
  elif cfg.tim15BtPress:
    print('15minBt depress', flush=True)
    cfg.tim15BtPress = False
    td = time.time()-cfg.tim15BtT0
    if td>2 and not cfg.tim15Run:
      cfg.tim15First = True
    elif td>2 and cfg.tim15Run:
      cfg.tim15End   = True
  else:
    cfg.tim15BtPress = False
#-----------------------------------------------#

#-------------------------------#
#          INTERRUPTS           #
#*******************************#
def initTimInterrupts():
  GPIO.add_event_detect(cfg.pinTimerBt1, GPIO.BOTH, callback=timer90min_callback, bouncetime=70)
  time.sleep(1)  
  GPIO.add_event_detect(cfg.pinTimerBt2, GPIO.BOTH, callback=timer15min_callback, bouncetime=70)
  time.sleep(1)  

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                           ENABLE/SHUTDOWN                             #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

#use the power button and annother button
#to perform the enable/turnoff
#to enale click the power button for 4 seconds
#to shutdown (which should be rare) click the 
#power button for 10 senconds
#device cant be turned off while alarmapp is running
#becahse this service is killed before alarm main and 
#restarted after it terminates

#-------------------------------#
#             LOOP              #
#*******************************#
def initIdleMode():
  print("starting idle mode")
  GPIO.output(cfg.pinPowerLed, 0)
  cfg.pwrBtPress  = False
  cfg.matCleared  = False
  cfg.pwrCntDispT = time.time()
  cfg.idleT0      = time.time()
  mat.clear8Mat()
  mat.fill16Mat(0)
  cfg.switchModes = False
#-----------------------------------------------#

def idleLoop():
  if cfg.idleFlag:
    if cfg.switchModes:
      initIdleMode()

    if cfg.pwrBtPress:
      GPIO.output(cfg.pinPowerLed, 1)

      if not cfg.matCleared:
        mat.fill16Mat(0)
        cfg.matCleared = True
      if((time.time()-cfg.pwrCntDispT)>0.2):
        mat.dispNumber(time.time()-cfg.idleT0)
        cfg.pwrCntDispT = time.time()

    else:
      if cfg.matCleared:
        mat.fill16Mat(0)
        cfg.matCleared = False
      GPIO.output(cfg.pinPowerLed, 0)
      mat.dispTime()
    
#-----------------------------------------------#

def power_callback(chan):
  if not GPIO.input(cfg.pinPowerBt) and not cfg.pwrBtPress:
    print('pwrBt press', flush=True)
    cfg.pwrBtPress = True
    cfg.idleT0     = time.time()
  #elif GPIO.input(cfg.pinPowerBt) and cfg.pwrBtPress:
  elif cfg.pwrBtPress:
    print('pwrBt depress', flush=True)
    cfg.pwrBtPress = False
    td = time.time()-cfg.idleT0
    if td>10:
      cfg.shutDownFlag = True
    elif td>2:
      if not cfg.switchModes and cfg.idleFlag: 
        switchGlucMode()
      if not cfg.switchModes and cfg.glucFlag:#TODO -- not alarm sounding 
        switchIdleMode()
    else:
      print('pwrBt press dur {:8.2f}'.format(td), flush=True)
  else:
    cfg.pwrBtPress = False
#-----------------------------------------------#

#-------------------------------#
#          INTERRUPTS           #
#*******************************#
def initPwdInterrupts():
  GPIO.add_event_detect(cfg.pinPowerBt, GPIO.BOTH, callback=power_callback, bouncetime=70)
  time.sleep(1)  

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              GLUCALARM                                #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

def initGlucMode():
  print('Terminating idle mode, starting Glucalarm', flush=True)
  mat.clear8Mat()
  mat.fill16Mat(0)
  time.sleep(1)
  mat.dispGluc()
  time.sleep(2)
  cfg.switchModes = False
#-----------------------------------------------#

def glucLoop():
  if cfg.glucFlag:
    if cfg.switchModes:
      initGlucMode()
    else:
      cgm.queryCgmData()
      if
      bs
      mat.dispBsArr()
      mat.printArrow()    


#-----------------------------------------------#

def checkAlarm(chan):
  if
   asd
asd
as
asd
asd
asd
asd
asdasda
asd
asd
asasd
asd
asd
asd d:dhasdhasd
asd
asd kadsjasdasdcfg.wack1Flag = True
#-----------------------------------------------#

def wack1_callback(chan):
  cfg.wack1Flag = True
#-----------------------------------------------#

def wack2_callback(chan):
  cfg.wack2Flag = True
#-----------------------------------------------#

def wack3_callback(chan):
  cfg.wack3Flag = True
#-----------------------------------------------#

#-------------------------------#
#          INTERRUPTS           #
#*******************************#
def initGlucInterrupts():
  GPIO.add_event_detect(cfg.pinWackBt1, GPIO.FALLING, callback=wack1_callback, bouncetime=70)
  time.sleep(1)  
  GPIO.add_event_detect(cfg.pinWackBt2, GPIO.FALLING, callback=wack2_callback, bouncetime=70)
  time.sleep(1)
  GPIO.add_event_detect(cfg.pinWackBt3, GPIO.FALLING, callback=wack3_callback, bouncetime=70)
  time.sleep(1)

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                                MAIN                                   #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#


def main():

  initServ()

  while True:
    if cfg.shutDownFlag:
      shutDown()
    else:
    timerServices()
    idleLoop()
    glucLoop()

#-----------------------------------------------#

def initServ():
  #init pi state
  cfg.init()
 # initPiState.initPi()
  mat.clear8Mat()
  mat.clear16Mat()

  #init state machine flags
  switchIdleMode()

  #init idle mode
  #initIdleMode()
  #initGlucMode()
  
  #init timers
  initTimer90()
  initTimer15()

  #define interrupt callbacks
  initPwdInterrupts()
  initTimInterrupts()
  initGlucInterrupts()
#-----------------------------------------------#

def switchGlucMode():
  cfg.switchModes = True
  cfg.idleFlag    = False
  cfg.glucFlag    = True
#-----------------------------------------------#

def switchIdleMode():
  cfg.switchModes = True
  cfg.idleFlag    = True
  cfg.glucFlag    = False
#-----------------------------------------------#

def shutDown():
  mat.dispShd()
  print('shutting down glucalarm', flush=True)
  time.sleep(2)
  #subprocess.call("sudo shutdown now", shell=True)
#-----------------------------------------------#

if __name__ == "__main__":
  #if ran as script
  main()
#-----------------------------------------------#

#EOF#
