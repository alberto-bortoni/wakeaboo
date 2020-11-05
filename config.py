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
#       define gpio        #
#**************************#
#process variables
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

#timers (T->B)
pinTimerBt1 = 17
pinTimerBt2 = 27

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
timerFlag    = False
shutDownFlag = False

#-------timer alarms------#
#init pi state
tim90BtT0    = time.time()

#trun on led
tim90BtPress = False
tim90Run     = False
tim90Finish  = False
tim90Last    = time.time()
tim90Start   = time.time()
tim90Dur     = 5400
tim90First   = False
tim90End     = False

#init pi state
tim15BtT0    = time.time()

#trun on led
tim15BtPress = False
tim15Run     = False
tim15Finish  = False
tim15Last    = time.time()
tim15Start   = time.time()
tim15Dur     = 900
tim15First   = False
tim15End     = False

#-------enable shutD------#
#init pi state
idleT0 = time.time()

#trun on led
pwrBtPress  = False
matCleared  = False
pwrCntDispT = time.time()

#-------wack states-------#
#wack1Flag = False
#wack2Flag = False
#wack3Flag = False
wackNumPress = 0
wackPressed  = False
targetWack   = 1
numWacks     = 5

#-------alarm states-------#
bsHighFl    = False
bsLowFl     = False
bsUrLowFl   = False

alarmArmed  = False
alarmTigger = False
alarmSound  = False

#-------alarm refact-------#
bsValTrigger  = -1
soundTim      = datetime.now()
refacTim      = datetime.now()
soundKillTim  = 1



#--------------------------#
#         cgm vars         #
#**************************#
#bs variables
bsHighVal     = 250
bsLowVal      = 90
bsUrLowVal    = 50
bsHighThd     = 30
bsLowThd      = 10
bsUrLowThd    = 3
bsHighTim     = 90
bsLowTim      = 15
bsUrLowTim    = 5
bsHighTimSz   = 15
bsLowTimSz    = 5
bsUrLowTimiSz = 0

# current BS state
rawImport = None # from nighscout
bsTime    = datetime.now()
bsValue   = 0     # mg/dl
bsTrend   = "nan" # text form
bsDirec   = "nan" # up; +45; hor; -45; dwn
bsDrop    = 0     # 0:noSpeed 1:oneArrow 2:twoArrow
bsData    = False # 0:noData  1:data
noDataTh  = 10    # no data treshold in min
timeStr   = None
cgmErr    = None  #TODO -- enum error
#TODO -- matrix display error to enum map


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
  GPIO.setup(pinTimerBt1, GPIO.IN)
  GPIO.setup(pinTimerBt2, GPIO.IN)

  #state of power button
  GPIO.setup(pinPowerBt, GPIO.IN)
  GPIO.setup(pinPowerLed, GPIO.OUT, initial=0)

  #highpower led
  GPIO.setup(pinHighPowerLed, GPIO.OUT, initial=0)

  #turn off led matrices
  mat.clear8Mat()
  mat.clear16Mat()

#if excecuted as script
if __name__=='__main__':
  init()

#EOF#
