#!/usr/bin/python3 -u

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import os
import time
import subprocess
from subprocess import PIPE, STDOUT
from datetime import datetime
from datetime import timedelta
import shlex
from time import sleep
import RPi.GPIO as GPIO
import config as cfg
import matrixDisplay as mat
import sys
import queryCgm as cgm
import random

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                             STARTUP STUFF                             #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                                 LAMP                                  #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

def lamp_callback(chan):
  GPIO.output(cfg.pinHighPowerLed, not GPIO.input(cfg.pinHighPowerLed))
#-----------------------------------------------#

#-------------------------------#
#          INTERRUPTS           #
#*******************************#
def initLampInterrupts():
  GPIO.add_event_detect(cfg.pinLampBt, GPIO.FALLING, callback=lamp_callback, bouncetime=300)
  time.sleep(1)



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              SWITCH MODE                              #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

def switchMode_callback(chan):
  if not cfg.switchModes and cfg.idleFlag:
    switchGlucMode()
  if not cfg.switchModes and cfg.glucFlag and not cfg.alarmTrigger and not cfg.alarmSound:
    switchIdleMode()
#-----------------------------------------------#

#-------------------------------#
#          INTERRUPTS           #
#*******************************#
def initModeInterrupts():
  GPIO.add_event_detect(cfg.pinModeBt, GPIO.FALLING, callback=switchMode_callback, bouncetime=300)
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
  print('Terminating Glucalarm, starting Idle mode', flush=True)
  GPIO.output(cfg.pinPowerLed, 0)
  cfg.pwrBtPress  = False
  cfg.matCleared  = False
  cfg.pwrCntDispT = time.time()
  cfg.idleT0      = time.time()
  mat.clear8Mat()
  mat.fill16Mat(0)
  time.sleep(1)
  mat.dispTim()
  time.sleep(2)
  mat.fill16Mat(0)
  cfg.switchModes = False
#-----------------------------------------------#

def idleLoop():
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
  print('Terminating Idle mode, starting Glucalarm', flush=True)
  cfg.targetWack = random.randint(0,2)
  mat.clear8Mat()
  mat.fill16Mat(0)
  time.sleep(1)
  mat.dispGluc()
  time.sleep(2)
  cfg.switchModes  = False
  cfg.bsHighFl     = False
  cfg.bsLowFl      = False
  cfg.bsUrLowFl    = False
  cfg.wackPressed  = False
  cfg.alarmTrigger = False
  cfg.alarmArmed   = False
  cfg.alarmSound   = False
  cfg.queryTim     = datetime.now()
#-----------------------------------------------#

def glucLoop():
  cgmLoop()

  if not cfg.bsData:
    noDataError()
  else:
    mat.dispBsArr()
    mat.printArrow()

    #normal
    if not cfg.alarmTrigger and not cfg.alarmArmed and not cfg.alarmSound:
      checkAlarm()
      alarmAction()
    
    #alarm sound/snooze (thresholds not checking during this time)
    elif cfg.alarmTrigger and not cfg.alarmArmed and cfg.alarmSound:
      if (datetime.now() < cfg.soundTim):
        playWack()
      elif (datetime.now() > cfg.soundTim):
        snoozeAlarm()

    #alarm snooze mode check/re-trigger
    elif not cfg.alarmTrigger and cfg.alarmArmed and cfg.alarmSound:
      if (datetime.now() < cfg.snoozeTim):
        checkSnoozeAlarm()
        alarmAction()
      elif (datetime.now() > cfg.snoozeTim):
        cfg.alarmArmed = False
        cfg.alarmSound = False
        print('snooze time met, re-triggering alarm')
        alarmAction()

    #alarm armed/back to normal
    elif not cfg.alarmTrigger and cfg.alarmArmed and not cfg.alarmSound:
      if (datetime.now() < cfg.refacTim):
        checkPostAlarm()
        alarmAction()
      elif (datetime.now() > cfg.refacTim):
        print('refactory time met, alarm not armed, back to normal')
        cfg.alarmArmed = False
        cfg.bsHighFl   = False
        cfg.bsLowFl    = False
        cfg.bsUrLowFl  = False

#-----------------------------------------------#

def cgmLoop():
  if(datetime.now()>(cfg.queryTim + timedelta(seconds=cfg.queryInt))):
    cgm.queryCgmData()
    cfg.queryTim = datetime.now()
    print('BS Value: %d'%(cfg.bsValue))
    print('Trig: %d, Armed: %d, Sound: %d'%(cfg.alarmTrigger, cfg.alarmArmed, cfg.alarmSound))
#-----------------------------------------------#

def checkAlarm():
  tmp = 'nan'

  if cfg.bsValue>=cfg.bsHighVal:
    cfg.bsHighFl  = True
    cfg.bsLowFl   = False
    cfg.bsUrLowFl = False
    tmp           = 'High'
    cfg.refacTim  = datetime.now() + timedelta(minutes=cfg.bsHighTim)

  elif cfg.bsValue<=cfg.bsLowVal and cfg.bsValue>cfg.bsUrLowVal:
    cfg.bsHighFl  = False
    cfg.bsLowFl   = True
    cfg.bsUrLowFl = False
    tmp           = 'Low'
    cfg.refacTim  = datetime.now() + timedelta(minutes=cfg.bsLowTim)

  elif cfg.bsValue<=cfg.bsUrLowVal:
    cfg.bsHighFl  = False
    cfg.bsLowFl   = False
    cfg.bsUrLowFl = True
    tmp           = 'Urgent Low'
    cfg.refacTim  = datetime.now() + timedelta(minutes=cfg.bsUrLowTim)


  if cfg.bsHighFl or cfg.bsLowFl or cfg.bsUrLowFl:
    print('bs val: %d'%(cfg.bsValue),'crossed threshold:',tmp,', refactory time',cfg.refacTim.strftime("%X"))
    cfg.alarmTrigger = True
    cfg.bsValTrigger = cfg.bsValue
#-----------------------------------------------#

def checkPostAlarm():
  if cfg.bsValue>=cfg.bsHighVal:
    if cfg.bsValue>=(cfg.bsValTrigger+cfg.bsHighThd) or not cfg.bsHighFl:
      cfg.bsHighFl     = True
      cfg.bsLowFl      = False
      cfg.bsUrLowFl    = False
      cfg.alarmTrigger = True
      cfg.alarmArmed   = False
      cfg.alarmSound   = False
      cfg.refacTim     = datetime.now() + timedelta(minutes=cfg.bsHighTim)
    
  elif cfg.bsValue<=cfg.bsLowVal and cfg.bsValue>cfg.bsUrLowVal:
    if cfg.bsUrLowFl:
      cfg.bsHighFl     = False
      cfg.bsLowFl      = True
      cfg.bsUrLowFl    = False
      cfg.refacTim     = datetime.now() + timedelta(minutes=cfg.bsLowTim)
      cfg.bsValTrigger = cfg.bsValue

    elif cfg.bsValue<=(cfg.bsValTrigger-cfg.bsLowThd) or not cfg.bsLowFl:
      cfg.bsHighFl     = False
      cfg.bsLowFl      = True
      cfg.bsUrLowFl    = False
      cfg.alarmTrigger = True
      cfg.alarmArmed   = False
      cfg.alarmSound   = False
      cfg.refacTim     = datetime.now() + timedelta(minutes=cfg.bsLowTim)

  elif cfg.bsValue<=cfg.bsUrLowVal:
    if cfg.bsValue<=(cfg.bsValTrigger-cfg.bsUrLowThd) or not cfg.bsUrLowFl:
      cfg.bsHighFl     = False
      cfg.bsLowFl      = False
      cfg.bsUrLowFl    = True
      cfg.alarmTrigger = True
      cfg.alarmArmed   = False
      cfg.alarmSound   = False
      cfg.refacTim     = datetime.now() + timedelta(minutes=cfg.bsUrLowTim)

  elif(cfg.bsValue<=cfg.bsInRangeH and cfg.bsValue>=cfg.bsInRangeL):
      cfg.alarmTrigger = False
      cfg.alarmArmed   = False
      cfg.alarmSound   = False
      cfg.bsHighFl     = False
      cfg.bsLowFl      = False
      cfg.bsUrLowFl    = False
      print('Bs Value of %d is in range, disarming and back to normal'%(cfg.bsValue))

  if cfg.alarmTrigger:
    print('Armed: new threshold exceeded while armed bs: %d'%(cfg.bsValue))
    cfg.bsValTrigger = cfg.bsValue
#-----------------------------------------------#

def checkSnoozeAlarm():
  if cfg.bsValue>=cfg.bsHighVal:
    if cfg.bsValue>=(cfg.bsValTrigger+cfg.bsHighThd):
      cfg.bsHighFl     = True
      cfg.bsLowFl      = False
      cfg.bsUrLowFl    = False
      cfg.alarmTrigger = True
      cfg.alarmArmed   = False
      cfg.alarmSound   = False

  elif cfg.bsValue<=cfg.bsLowVal and cfg.bsValue>cfg.bsUrLowVal:
    if cfg.bsValue<=(cfg.bsValTrigger-cfg.bsLowThd) and cfg.bsValue>(cfg.bsValTrigger-cfg.bsUrLowThd):
      cfg.bsHighFl     = False
      cfg.bsLowFl      = True
      cfg.bsUrLowFl    = False
      cfg.alarmTrigger = True
      cfg.alarmArmed   = False
      cfg.alarmSound   = False

  elif cfg.bsValue<=cfg.bsUrLowVal:
    if cfg.bsValue<=(cfg.bsValTrigger-cfg.bsUrLowThd):
      cfg.bsHighFl     = False
      cfg.bsLowFl      = False
      cfg.bsUrLowFl    = True
      cfg.alarmTrigger = True
      cfg.alarmArmed   = False
      cfg.alarmSound   = False
  
  if cfg.alarmTrigger:
    print('Snooze: threshold exceeded while in snooze mode')
    cfg.bsValTrigger = cfg.bsValue
#-----------------------------------------------#

def alarmAction():
  #sound alarm
  if cfg.alarmTrigger and not cfg.alarmSound:
    cfg.alarmSound  = True
    cfg.soundTim    = datetime.now() + timedelta(minutes=cfg.soundKillTim)

    if cfg.bsHighFl:
      print('high alarm')
      #TODO -- sound
    elif cfg.bsLowFl:
      print('low alarm')
      #TODO -- sound
    elif cfg.bsUrLowFl:
      print('UrLow alarm')
      #TODO -- sound

    #trun first wack on
    resetWackCnt()
    cfg.targetWack  = (cfg.targetWack + random.randint(1,2))%3
    cfg.wackPressed = False
    trunWackLed()
#-----------------------------------------------#

def playWack():
  if cfg.wackPressed and (cfg.numWacks != 0):
    if cfg.wackNumPress == cfg.targetWack:
      cfg.numWacks    = cfg.numWacks-1
      cfg.targetWack  = (cfg.targetWack + random.randint(1,2))%3
      cfg.wackPressed = False
      print('Correct wack pressed, next %d, remaining %d'%(cfg.targetWack, cfg.numWacks))
      trunWackLed()

    elif cfg.wackNumPress != cfg.targetWack:
      resetWackCnt()
      turnAllLed(1)
      time.sleep(1)
      turnAllLed(0)
      time.sleep(1)
      turnAllLed(1)
      time.sleep(1)
      turnAllLed(0)
      cfg.targetWack  = (cfg.targetWack + random.randint(1,2))%3
      cfg.wackPressed = False
      print('Wrong wack pressed, next %d, remaining %d'%(cfg.targetWack, cfg.numWacks))
      trunWackLed()

  elif cfg.wackPressed and (cfg.numWacks == 0):
    cfg.wackPressed  = False
    turnAllLed(1)
    time.sleep(1)
    turnAllLed(0)
    print('finished wack game')
    ackAlarm()
#-----------------------------------------------#

def noDataError():
  cfg.bsHighFl     = False
  cfg.bsLowFl      = False
  cfg.bsUrLowFl    = False
  cfg.wackPressed  = False
  cfg.alarmTrigger = False
  cfg.alarmArmed   = False
  cfg.alarmSound   = False
  mat.dispErr()
#-----------------------------------------------#

def snoozeAlarm():
  cfg.numWacks     = 0
  cfg.wackPressed  = False

  turnAllLed(1)
  time.sleep(1)
  turnAllLed(0)

  cfg.alarmTrigger = False
  cfg.alarmArmed   = True
  cfg.alarmSound   = True

  #TODO -- kill alarm

  if cfg.bsHighFl:
    cfg.snoozeTim  = datetime.now() + timedelta(minutes=cfg.bsHighTimSz)
  elif cfg.bsLowFl:
    cfg.snoozeTim  = datetime.now() + timedelta(minutes=cfg.bsLowTimSz)
  elif cfg.bsUrLowFl:
    cfg.snoozeTim  = datetime.now() + timedelta(minutes=cfg.bsUrLowTimSz)
  print('alarmed sounded for a while, arming and snoozing until', cfg.soundTim.strftime("%X"))
#-----------------------------------------------#

def ackAlarm():
  cfg.ackTim = datetime.now()

  cfg.alarmSound   = False
  cfg.alarmTrigger = False
  cfg.alarmArmed   = True

  #TODO -- kill alarm

  if cfg.bsHighFl:
    tmp = cfg.bsValTrigger+cfg.bsHighThd
  elif cfg.bsLowFl:
    tmp = cfg.bsValTrigger-cfg.bsUrLowThd
  elif cfg.bsUrLowFl:
    tmp = cfg.bsValTrigger-cfg.bsLowThd

  print('Alarm ack: armed until:', cfg.refacTim.strftime("%X"), 'or bs in range, unless a bs value of: %d '%(tmp))
#-----------------------------------------------#

def turnAllLed(val):
  GPIO.output(cfg.pinWackLed1, val)
  GPIO.output(cfg.pinWackLed2, val)
  GPIO.output(cfg.pinWackLed3, val)
#-----------------------------------------------#

def trunWackLed():
  GPIO.output(cfg.pinWackLed1, 0)
  GPIO.output(cfg.pinWackLed2, 0)
  GPIO.output(cfg.pinWackLed3, 0)

  if cfg.targetWack == 0:
    GPIO.output(cfg.pinWackLed1, 1)
  elif cfg.targetWack == 1:
    GPIO.output(cfg.pinWackLed2, 1)
  elif cfg.targetWack == 2:
    GPIO.output(cfg.pinWackLed3, 1)
#-----------------------------------------------#

def resetWackCnt():
  if cfg.bsHighFl:
    cfg.numWacks  = 5
  elif cfg.bsLowFl:
    cfg.numWacks  = 3
  elif cfg.bsUrLowFl:
    cfg.numWacks  = 1
  else:
    cfg.numWacks  = 5
#-----------------------------------------------#

def wack1_callback(chan):
  cfg.wackNumPress = 0
  if cfg.alarmTrigger:
    cfg.wackPressed = True
#-----------------------------------------------#

def wack2_callback(chan):
  cfg.wackNumPress = 1
  if cfg.alarmTrigger:
    cfg.wackPressed = True
#-----------------------------------------------#

def wack3_callback(chan):
  cfg.wackNumPress = 2
  if cfg.alarmTrigger:
    cfg.wackPressed = True
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


    elif cfg.idleFlag:
      if cfg.switchModes:
        initIdleMode()
      idleLoop()


    elif cfg.glucFlag:
      if cfg.switchModes:
        initGlucMode()
      else:
        glucLoop()
#-----------------------------------------------#

def initServ():
  #init pi state
  cfg.init()
  mat.clear8Mat()
  mat.clear16Mat()

  #init state machine flags
  #switchIdleMode()
  switchGlucMode()

  #define interrupt callbacks
  initPwdInterrupts()
  initLampInterrupts()
  initModeInterrupts()
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
  mat.clear8Mat()
  mat.fill16Mat(0)
  subprocess.call("sudo shutdown now", shell=True)
#-----------------------------------------------#

if __name__ == "__main__":
  #if ran as script
  main()
#-----------------------------------------------#
#EOF#
