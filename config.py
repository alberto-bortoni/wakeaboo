#! /usr/bin/python3

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import os
import time
from datetime import datetime
from datetime import timedelta
import board
import numpy as np
import RPi.GPIO as GPIO
import matrixDisplay as mat


#--------------------------#
#         process          #
#**************************#
printDebug = False


#--------------------------#
#       define gpio        #
#**************************#
#wack buttons (R->L)
pinWackBt1  = 26
pinWackBt2  = 13
pinWackBt3  = 19
pinWackLed1 = 20
pinWackLed2 = 21
pinWackLed3 = 16

#GPIO buttons (T->B)
pinLampBt = 17
pinModeBt = 27

#power button
pinPowerBt  = 22
pinPowerLed = 24

#highpowerLED
pinHighPowerLed = 18

#matrices
disp16Add = 0x71
disp8Add  = 0x70


#--------------------------#
#       runtime vars       #
#**************************#

#-------state flags--------#
switchModes  = False
idleFlag     = False
glucFlag     = False
shutDownFlag = False

#---------servTim----------#
idleServTim = time.time()
idleTimInt  = 1
shdServTim  = time.time()
shdTimInt   = 0.5

#-------enable shutD------#
powerTim    = time.time()
pwrBtPress  = False

#-------wack states-------#
wackNumPress = 0
wackPressed  = False
targetWack   = 1
numWacks     = 5

#--------alarm sound-------#
alarmVol     = 10
alarmVolSt   = 2
alarmVolMax  = 110
alarmVolMin  = 30
alarmIncTim  = 5 
alarmTimLast = time.time()

#------alarm locatio-------#
highAlarmFile   = "/home/boo/glucalarm/music/highAlarm.mp3"
lowAlarmFile    = "/home/boo/glucalarm/music/lowAlarm.mp3"
urLowAlarmFile  = "/home/boo/glucalarm/music/urLowAlarm.mp3"
dropAlarmFile   = "/home/boo/glucalarm/music/dropAlarm.mp3"
errorAlarmFile  = "/home/boo/glucalarm/music/errorAlarm.mp3"

#-------alarm states-------#
bsHighFl    = False
bsLowFl     = False
bsUrLowFl   = False
bsDrop1Fl   = False
bsDrop2Fl   = False

alarmMsg    = False
alarmSound  = False

#-------alarm refact-------#
soundTim      = datetime.now()
soundKillTim  = 60 #in sec

#-------gluc refact--------#
glucStopTim = 11 #am
glucTim     = datetime.now()

#--------------------------#
#         cgm vars         #
#**************************#
#bs variables
bsHighTrigr  = 280
bsHighReset  = 180
bsHighLatch  = False

bsLowTrigr   = 90
bsLowReset   = 100
bsLowLatch   = False

bsUrLowTrigr = 55
bsUrLowReset = 65
bsUrLowLatch = False

bsDrop2Trigr = 120 
drop2Trigr   = 23
drop2Reset   = 20
bsDrop2Latch = False

bsDrop1Trigr = 100 
drop1Trigr   = 22
drop1Reset   = 20
bsDrop1Latch = False


#current BS state
rawImport = None # from nighscout
bsTime    = datetime.now()
bsValue   = 0     # mg/dl
bsTrend   = "nan" # text form
bsDirec   = "nan" # up; +45; hor; -45; dwn
bsDrop    = 99    # 23,22;21;20;19;18,17 first is dir, second is arrow
bsData    = False # 0:noData  1:data
noDataTh  = 10    # min. if older then error
timeStr   = None
cgmErr    = None  #TODO -- enum error
#TODO -- matrix display error to enum map

#query state
queryInt  = 20 #in seconds
queryTim  = datetime.now()

#no data
noDataFl    = False
noDataLatch = False
noDataInt   = datetime.now()
noDataTim   = 10  #min. if error for this long, sound

#--------------------------#
#          matrix          #
#**************************#
ledmat = np.zeros((8,16))
arrmat = np.zeros((8,8))


#--------------------------#
#        init state        #
#**************************#

def init():
  #set gpio mode
  GPIO.setmode(GPIO.BCM)

  #state of wack buttons/leds
  GPIO.setup(pinWackBt1, GPIO.IN)
  GPIO.setup(pinWackBt2, GPIO.IN)
  GPIO.setup(pinWackBt3, GPIO.IN)
  GPIO.setup(pinWackLed1, GPIO.OUT, initial=0)
  GPIO.setup(pinWackLed2, GPIO.OUT, initial=0)
  GPIO.setup(pinWackLed3, GPIO.OUT, initial=0)

  #state of timer buttons
  GPIO.setup(pinLampBt, GPIO.IN)
  GPIO.setup(pinModeBt, GPIO.IN)

  #state of power button
  GPIO.setup(pinPowerBt, GPIO.IN)
  GPIO.setup(pinPowerLed, GPIO.OUT, initial=0)

  #highpower led
  GPIO.setup(pinHighPowerLed, GPIO.OUT, initial=0)

  #turn off led matrices
  mat.setDisp8Brightness(1)
  mat.setDisp16Brightness(0)
  mat.clear8Mat()
  mat.clear16Mat()

#if excecuted as script
if __name__=='__main__':
  init()

#EOF#
