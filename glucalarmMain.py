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
#                                 LAMP                                  #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

#```````````````````````````````````````````````#
# turn lamp LED by toggoling state              #
#_______________________________________________#
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

#```````````````````````````````````````````````#
# switch between clock and gluc unless alarm on #
#_______________________________________________#
def switchMode_callback(chan):
  if not cfg.switchModes and cfg.idleFlag:
    switchGlucMode()
  if not cfg.switchModes and cfg.glucFlag and not cfg.alarmSound:
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

#```````````````````````````````````````````````#
# to shutdown (which should be rare) click the  #
# power button for 10 senconds                  #
# device cant be turned off while alarm is run  #
#_______________________________________________#

#```````````````````````````````````````````````#
# initialize idle clock mode                    #
#_______________________________________________#
def initIdleMode():
  print('Terminating Glucalarm, starting Idle mode')
  GPIO.output(cfg.pinPowerLed, 0)
  cfg.pwrBtPress  = False
  cfg.pwrCntDispT = time.time()
  cfg.powerTim    = time.time()
  mat.clear8Mat()
  mat.fill16Mat(0)
  time.sleep(1)
  mat.dispTim()
  time.sleep(2)
  mat.fill16Mat(0)
  cfg.switchModes = False
#-----------------------------------------------#

#```````````````````````````````````````````````#
# idle clock main loop                          #
#_______________________________________________#
def idleLoop():
  mat.dispTime()

#-----------------------------------------------#

#```````````````````````````````````````````````#
# timer to call shutdown routine                #
#_______________________________________________#
def shutdownMode():
  if cfg.pwrBtPress:
    GPIO.output(cfg.pinPowerLed, 1)

    td = time.time()-cfg.powerTim
    if td>10:
      cfg.shutDownFlag = True
    else:
      print('pwrBt press dur {:8.2f}'.format(td))
  else:
    GPIO.output(cfg.pinPowerLed, 0)
#-----------------------------------------------#

#```````````````````````````````````````````````#
# interrupt to power off                        #
#_______________________________________________#
def power_callback(chan):
  if not GPIO.input(cfg.pinPowerBt):
    cfg.powerTim    = time.time()
    cfg.pwrBtPress  = True
  else:
    cfg.pwrBtPress  = False
#-----------------------------------------------#

#-------------------------------#
#          INTERRUPTS           #
#*******************************#
def initPwdInterrupts():
  GPIO.add_event_detect(cfg.pinPowerBt, GPIO.BOTH, callback=power_callback, bouncetime=100)
  time.sleep(1)


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              GLUCALARM                                #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

#```````````````````````````````````````````````#
# initialize the glucalarm mode                 #
#_______________________________________________#
def initGlucMode():
  print('Terminating Idle mode, starting Glucalarm', flush=True)
  cfg.targetWack = random.randint(0,2)
  mat.clear8Mat()
  mat.fill16Mat(0)
  time.sleep(1)
  mat.dispGluc()
  time.sleep(1)
  cfg.switchModes  = False
  cfg.bsHighFl     = False
  cfg.bsHighLatch  = False
  cfg.bsLowFl      = False
  cfg.bsLowLatch   = False
  cfg.bsUrLowFl    = False
  cfg.bsUrLowLatch = False
  cfg.bsDrop2Fl    = False
  cfg.bsFrop2Latch = False
  cfg.bsDrop1Fl    = False
  cfg.bsFrop1Latch = False
  cfg.wackPressed  = False
  cfg.alarmSound   = False
  cfg.noDataLatch  = False
  cfg.soundTim     = datetime.now()
  cfg.queryTim     = datetime.now()
  cfg.noDataTim    = datetime.now()
  cfg.glucTim      = datetime.now()
  if (cfg.glucTim.hour < cfg.glucStopTim):
    cfg.glucTim.replace(hour=cfg.glucStopTim)
  else:
    cfg.glucTim = cfg.glucTim + timedelta(days=1)
    cfg.glucTim.replace(hour=cfg.glucStopTim)
#-----------------------------------------------#

#```````````````````````````````````````````````#
#  main glucalarm loop. query, display, alarm   #
#_______________________________________________#
def glucLoop():
  cgmLoop()

  if not cfg.bsData:
    if not cfg.noDataFl:
      cfg.noDataFl  = True
      cfg.noDataTim = datetime.now() + timedelta(minutes=cfg.noDataInt)
      noDataError()
    elif(datetime.now() > cfg.noDataTim):
      cfg.noDataLatch = True
  else:
    mat.dispBsArr()
    mat.printArrow()
    checkAlarm()

  if (cfg.bsHighLatch or cfg.bsLowLatch or cfg.bsUrLowLatch or cfg.bsDrop2Latch or cfg.bsDrop1Latch or cfg.noDataLatch) and not cfg.alarmSound:
    alarmAction()
  elif cfg.alarmSound and (datetime.now() > cfg.soundTim):
    killAlarm()
  elif cfg.alarmSound:
    playWack()

#-----------------------------------------------#

#```````````````````````````````````````````````#
# get the cgm values at a query interval        #
#_______________________________________________#
def cgmLoop():
  if(datetime.now() > cfg.queryTim):
    cgm.queryCgmData()
    cfg.queryTim = datetime.now() + timedelta(seconds=cfg.queryInt)
    if cfg.printDebug:
      print('bs: %d, S: %d, H: %d, HL: %d, L: %d, LL: %d, Ur: %d, UrL: %d, D2: %d, D2L: %d, D1: %d, D1L: %d'%(cfg.bsValue, cfg.alarmSound, cfg.bsHighFl, cfg.bsHighLatch, cfg.bsLowFl, cfg.bsLowLatch, cfg.bsUrLowFl, cfg.bsUrLowLatch, cfg.bsDrop2Fl,cfg.bsDrop2Latch, cfg.bsDrop1Fl, cfg.bsDrop1Latch))
#-----------------------------------------------#

#```````````````````````````````````````````````#
# logic behind what alarm to sound according to #
# bs or no data. turn the latch and flags       #
#_______________________________________________#
def checkAlarm():
  tmp = 'nan'
  
  #check for urgent low
  if cfg.bsValue<=cfg.bsUrLowTrigr and not cfg.bsUrLowFl:
    cfg.bsLowFl      = True
    cfg.bsLowLatch   = False
    cfg.bsUrLowFl    = True
    cfg.bsUrLowLatch = True
    tmp              = 'Urgent Low'
    cfg.alarmMsg     = True 
  elif cfg.bsValue > cfg.bsUrLowReset and cfg.bsUrLowFl:
    cfg.bsUrLowFl    = False
    cfg.bsUrLowLatch = False
    tmp              = 'Not Urgent Low'
    cfg.alarmMsg     = True 

  #check for low
  if (cfg.bsValue<=cfg.bsLowTrigr and cfg.bsValue>cfg.bsUrLowTrigr) and not (cfg.bsLowFl or cfg.bsUrLowFl):
    cfg.bsLowFl      = True
    cfg.bsLowLatch   = True
    tmp              = 'Low'
    cfg.alarmMsg     = True 
  elif cfg.bsValue > cfg.bsLowReset and cfg.bsLowFl:
    cfg.bsLowFl      = False
    cfg.bsLowLatch   = False
    tmp              = 'Not Low'
    cfg.alarmMsg     = True 
  
  #check for high bs
  if cfg.bsValue>=cfg.bsHighTrigr and not cfg.bsHighFl:
    cfg.bsHighFl     = True
    cfg.bsHighLatch  = True
    tmp              = 'High'
    cfg.alarmMsg     = True
  elif cfg.bsValue < cfg.bsHighReset and cfg.bsHighFl:
    cfg.bsHighFl     = False
    cfg.bsHighLatch  = False
    tmp              = 'Not High'
    cfg.alarmMsg     = True 

  #check for double drop
  if (cfg.bsValue<=cfg.bsDrop2Trigr and cfg.bsDrop==cfg.drop2Trigr) and not (cfg.bsLowFl or cfg.bsUrLowFl or cfg.bsDrop2Fl or cfg.bsDrop1Fl):
    cfg.bsDrop1Fl    = True
    cfg.bsDrop1Latch = True
    cfg.bsDrop2Fl    = True
    cfg.bsDrop2Latch = True
    tmp              = 'Fast 2 Drop'
    cfg.alarmMsg     = True 
  elif cfg.bsDrop > cfg.drop2Reset and cfg.bsDrop2Fl:
    cfg.bsDrop2Fl    = False
    cfg.bsDrop2Latch = False
    tmp              = 'Not Droping'
    cfg.alarmMsg     = True 

  #check for single drop
  if (cfg.bsValue<=cfg.bsDrop1Trigr and cfg.bsDrop==cfg.drop1Trigr) and not (cfg.bsLowFl or cfg.bsUrLowFl or cfg.bsDrop2Fl or cfg.bsDrop1Fl):
    cfg.bsDrop1Fl    = True
    cfg.bsDrop1Latch = True
    tmp              = 'Fast 1 Drop'
    cfg.alarmMsg     = True 
  elif cfg.bsDrop > cfg.drop1Reset and cfg.bsDrop1Fl:
    cfg.bsDrop1Fl    = False
    cfg.bsDrop1Latch = False
    tmp              = 'Not Droping'
    cfg.alarmMsg     = True 

  #send msg
  if cfg.alarmMsg:
    print('bs val: %d'%(cfg.bsValue),' Bs state:',tmp)
    cfg.alarmMsg = False
#-----------------------------------------------#

#```````````````````````````````````````````````#
# sound alarm mplayer according to flag         #
#_______________________________________________#
def alarmAction():
  #sound alarm
  cfg.alarmSound  = True
  cfg.soundTim    = datetime.now() + timedelta(seconds=cfg.soundKillTim)

  if cfg.bsUrLowFl and cfg.bsUrLowLatch:
    cfg.bsUrLowLatch = False
    print('UrLow alarm')
    #TODO -- sound
  elif cfg.bsLowFl and cfg.bsLowLatch:
    cfg.bsLowLatch   = False
    print('low alarm')
    #TODO -- sound
  elif cfg.bsHighFl and cfg.bsHighLatch:
    cfg.bsHighLatch  = False
    print('high alarm')
    #TODO -- sound
  elif cfg.bsDrop1Fl and cfg.bsDrop1Latch:
    cfg.bsDrop1Latch = False
    print('fast 1 drop alarm')
    #TODO -- sound
  elif cfg.bsDrop2Fl and cfg.bsDrop2Latch:
    cfg.bsDrop2Latch = False
    print('fast 2 drop alarm')
    #TODO -- sound
  elif cfg.noDataFl and cfg.noDataLatch:
    cfg.noDataLatch  = False
    print('no data alarm')
    #TODO -- sound

  #trun first wack on
  initWackPlay()
#-----------------------------------------------#

#```````````````````````````````````````````````#
# begin to play wack by getting a target        #
#_______________________________________________#
def initWackPlay():
  #trun first wack on
  resetWackCnt()
  cfg.targetWack  = (cfg.targetWack + random.randint(1,2))%3
  cfg.wackPressed = False
  trunWackLed()
#-----------------------------------------------#

#```````````````````````````````````````````````#
# turn a random wack on and expect to press     #
# results in ack alarm
#_______________________________________________#
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
    print('finished wack game')
    ackAlarm()
#-----------------------------------------------#

#```````````````````````````````````````````````#
# clear many flags if there is no data error    #
#_______________________________________________#
def noDataError():
  cfg.bsHighFl     = False
  cfg.bsHighLatch  = False
  cfg.bsLowFl      = False
  cfg.bsLowLatch   = False
  cfg.bsUrLowFl    = False
  cfg.bsUrLowLatch = False
  cfg.bsDrop2Fl    = False
  cfg.bsFrop2Latch = False
  cfg.bsDrop1Fl    = False
  cfg.bsFrop1Latch = False
  cfg.wackPressed  = False
  cfg.alarmSound   = False
  mat.dispErr()
#-----------------------------------------------#

#```````````````````````````````````````````````#
# ack alarm and kill alarm subrpcess mplayer    #
#_______________________________________________#
def ackAlarm():
  cfg.alarmSound   = False
  cfg.wackPressed  = False
  turnAllLed(1)
  time.sleep(1)
  turnAllLed(0)

  #TODO -- kill alarm

  print('Alarm ack, latched until Bs in range bs val: %d'%(cfg.bsValue))
#-----------------------------------------------#

#```````````````````````````````````````````````#
# kill alarm subprocess mplayer                 #
#_______________________________________________#
def killAlarm():
  cfg.alarmSound   = False
  cfg.wackPressed  = False
  turnAllLed(1)
  time.sleep(1)
  turnAllLed(0)

  #TODO -- kill alarm

  print('Alarm sounded for a while, kiiling it. bs val: %d'%(cfg.bsValue))
#-----------------------------------------------#

#```````````````````````````````````````````````#
# trun all wack leds on                         #
#_______________________________________________#
def turnAllLed(val):
  GPIO.output(cfg.pinWackLed1, val)
  GPIO.output(cfg.pinWackLed2, val)
  GPIO.output(cfg.pinWackLed3, val)
#-----------------------------------------------#

#```````````````````````````````````````````````#
# trun the target wack led on                   #
#_______________________________________________#
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

#```````````````````````````````````````````````#
# get how many times you need to wack to ack    #
#_______________________________________________#
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

#```````````````````````````````````````````````#
# interrupts to get wack button state           #
#_______________________________________________#
def wack1_callback(chan):
  cfg.wackNumPress = 0
  if (cfg.bsHighFl or cfg.bsLowFl or cfg.bsUrLowFl) and cfg.alarmSound:
    cfg.wackPressed = True
#-----------------------------------------------#

def wack2_callback(chan):
  cfg.wackNumPress = 1
  if (cfg.bsHighFl or cfg.bsLowFl or cfg.bsUrLowFl) and cfg.alarmSound:
    cfg.wackPressed = True
#-----------------------------------------------#

def wack3_callback(chan):
  cfg.wackNumPress = 2
  if (cfg.bsHighFl or cfg.bsLowFl or cfg.bsUrLowFl) and cfg.alarmSound:
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
    if (time.time()-cfg.shdServTim)>cfg.shdTimInt:
      shdServTim = time.time()
      shutdownMode()
      if cfg.shutDownFlag:
        shutDown()

    if cfg.idleFlag:
      if cfg.switchModes:
        initIdleMode()
      elif (time.time()-cfg.idleServTim)>cfg.idleTimInt:
        idleServTim = time.time()
        idleLoop()


    elif cfg.glucFlag:
      if cfg.switchModes:
        initGlucMode()
      else:
        if(datetime.now() > cfg.glucTim):
          switchIdleMode()
        else:
          glucLoop()
#-----------------------------------------------#

#```````````````````````````````````````````````#
# initialize services, defaults to clock        #
#_______________________________________________#
def initServ():
  #init pi state
  cfg.init()
  mat.clear8Mat()
  mat.clear16Mat()

  #init state machine flags
  switchIdleMode()
  #switchGlucMode()

  #define interrupt callbacks
  initPwdInterrupts()
  initLampInterrupts()
  initModeInterrupts()
  initGlucInterrupts()
#-----------------------------------------------#

#```````````````````````````````````````````````#
# change between glugalarm and clock modes      #
#_______________________________________________#
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

#```````````````````````````````````````````````#
# call the shutdown subroutine                  #
#_______________________________________________#
def shutDown():
  mat.dispShd()
  print('shutting down glucalarm')
  time.sleep(2)
  mat.clear8Mat()
  mat.fill16Mat(0)
  GPIO.output(cfg.pinPowerLed, 0)
  GPIO.output(cfg.pinHighPowerLed, 0)
  turnAllLed(0)
  
  subprocess.call("sudo shutdown now", shell=True)
#-----------------------------------------------#

if __name__ == "__main__":
  #if ran as script
  main()
#-----------------------------------------------#
#EOF#
