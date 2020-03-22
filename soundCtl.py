#! /usr/bin/python3

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import mpylayer
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
from random import random


# first disable the shutdown routine and spotify
subprocess.call(["/etc/init.d/listen-for-shutdown.sh", "stop"])
#TODO -- disable spotify
# enable print
enablePrint = True #TODO -- make my print method

#################################
#          VARIABLES            #
#################################

# enable/disable functionality
startTime       = time.time() #TODO -- what is this, use for first junk data
lastTime        = time.time() #TODO -- what is this
buttRisingTime  = None
buttFallingTime = None
buttDuration    = None
disableTime     = 5 # press for in seconds
exitFlag        = False
prevBttnState   = False # to count time
disableBtLatch  = False # cant diactivate if alarm is on

#threshold for alarms
highBs   = 180
highUrBs = 200
highStBs = 30
highTime = 90 #min
lowBs    = 80
urLowBs  = 50
lowStBs  = 10
lowTime  = 10 #min


# current BS state
rawImport = None # from nighscout
bsTime    = datetime.now()
bsValue   = 0  # mg/dl
bsTrend   = 0  # 1:90up 2:45up 3:flat 4:45down 5:90down
bsDrop    = 0  # 0:noSpeed 1:oneArrow 2:twoArrow
bsDataAv  = False # 1:noData  1:data
noDataTh  = 10 # no data treshold in min
bsDataErr = 0  # 0:noerr, 1:wgeterr
timeStr   = None

# alarm variables
termLongTime  = 600 #10 min to auto ack

#player volume
volume      = 10
volumeStep  = 2
maxVol      = 110
minVol      = 30
incVolServ  = 1  #sec
lastVolInc  = datetime.now()

#aduio related stuff
alarmHigh   = "/home/boo/glucalarm/audio/"
alarmHighUr = "/home/boo/glucalarm/audio/"
alarmLow    = "/home/boo/glucalarm/audio/"
alarmLowUr  = "/home/boo/glucalarm/audio/"
alarmNoData = "/home/boo/glucalarm/audio/"
alarmDrop   = "/home/boo/glucalarm/audio/"
alarmRaise  = "/home/boo/glucalarm/audio/"

songs    = os.listdir(musicDir)
songsNum = len(songs)
randSong = randint(1, songsNum)-1

# target buttons and state
targetWack   = 0
targetLed    = 0
pressedWack  = False
wrongWack    = False
pendingPress = True 
totAckPress  = 0
highAckPress = 6
lowAckPress  = 4
uLowAckPress = 1
droppingAckPress = 1
risingAckPress   = 1

# timer variables
timerSet     = False
timerSetTime = 0

#loop services in seconds
bsServiceLoop    = 30
lastBsLoop       = datetime.now()
alarmTriggerTime = datetime.now()
bsValueTrigger   = 0
alarmTriggerFlag = False
alarmPrimedFlag  = False
highBsStateFlag  = False
lowBsStateFlag   = False
uLowBsStateFlag  = False
bsValueTrigger   = 0


#################################
#             GPIO              #
#################################
#hardware pin number for button
disableBt   =  5 #pin 29
wackBt1     = 21 #pin 40
wackBt2     = 20 #pin 38
wackBt3     = 16 #pin 36
wackBt4     = 19 #pin 35
wackBt5     = 26 #pin 37
wackLed1    = 17 #pin 11
wackLed2    = 27 #pin 13
wackLed3    = 22 #pin 15
wackLed4    = 23 #pin 16
wackLed5    = 24 #pin 18
timer15     = 12 #pin 32
timer90     = 13 #pin 33
elWire      =  9 #pin 21
roomLed     = 11 #pin 23
leds        = [17, 27, 22, 23, 24]
wacks       = [21, 20, 16, 19, 26]


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                           FUNCTIONS                                   #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#


#################################
#           ALARM              #
#################################


# increases volume by sending a character command to mplayer
# 0 is mplayer's command to increase
def increaseVolume():
  global volume, player, maxVol
  if (volume < maxVol):
    volume = volume + volumeStep
    print "Increasing volume to {}".format(volume)
    player.stdin.write('0')
    player.stdin.flush()
 #-----------------------------------------------#

# decreases volume by sending a character command to mplayer
# 9 is mplayer's command to decrease
def decreaseVolume():
  global volume, player, minVol
  if (volume > minVol):
    volume = volume - volumeStep
    print "Decreasing volume to {}".format(volume)
    player.stdin.write('9')
    player.stdin.flush()
 #-----------------------------------------------#
 
#alarm trigger
#type: 1urHigh 2high 3low 4urLow 5noData 6drop 7rise
def tirggerAlarm(alarmType)
  if alarmTriggerFlag:
    alarmTriggerFlag = False
    
    # boot player w prefered cmd
    if alarmType == 1:
      alarmSound = alarmHigh
    elif alarmType == 2:
      alarmSound = alarmHighUr
    elif alarmType == 3:
      alarmSound = alarmLow
    elif alarmType == 4:
      alarmSound = alarmLowUr
    elif alarmType == 5:
      alarmSound = alarmNoData
    elif alarmType == 6:
      alarmSound = alarmDrop
    elif alarmType == 7:
      alarmSound = alarmRaise

    player = subprocess.Popen(["mplayer", "-volume", "-1", "-volstep",
                          str(volumeStep), "-loop", "0", "-really-quiet",
                          alarmSound, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True)

    # delay to allow player to finalize initialization
    time.sleep(10)
 #-----------------------------------------------#



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                             MAIN                                      #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

#################################
#             START             #
#################################

# initialize mplayer with prefered condigurations and introduce a delay to allow it to boot correctly
# kill the subprocess after. This is a workaround to allow mplayer to actually start volume at the command sent
# otherwise it actually does not.
alarm = subprocess.Popen(["mplayer", "-volume", str(volume), "-really-quiet",
                         "/home/eleven/Alarms/Alarm03.wav"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
time.sleep(5)
alarm.terminate()

random.seed(a=None, version=2)


subprocess.call(["/etc/init.d/listen-for-shutdown.sh", "start"])

#EOF#
