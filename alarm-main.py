#! /usr/bin/python

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

# first disable the shutdown routine and spotify
subprocess.call(["/etc/init.d/listen-for-shutdown.sh", "stop"])
#TODO -- disable spotify


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
highbs   = 180
highurbs = 200
highstbs = 30
hightime = 90 #min
lowbs    = 80
lowurbs  = 50
lowstbs  = 10 
lowtime  = 10 #min

# current BS state
rawImport = None # from nighscout
bsTime    = time.time()
bsValue   = 0  # mg/dl
bsTrend   = 0  # 1:90up 2:45up 3:flat 4:45down 5:90down
bsDrop    = 0  # 0:noSpeed 1:oneArrow 2:twoArrow
bsData    = False # 0:noData  1:data
noDataTh  = 10 # no data treshold in min

# alarm variables
termLongTime  = 600 #10 min to auto ack 

#player volume
volume      = 10
volumeStep  = 2
maxVol      = 110
minVol      = 30
timeIncVol  = 1

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
targetWack  = 0
targetLed   = 0
pressedWack = False
wrongWack   = False

# timer variables
timerSet     = False
timerSetTime = 0


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




#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                         INIT  SETTINGS                                #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

#################################
#           GPIO INIT           #
#################################

# activates the GIPO on the Raspi as a pullup mode and defines its callback function
GPIO.setmode(GPIO.BCM)

# add rising edge detection on all buttons
GPIO.setup(disableBt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(timer15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(timer90, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# set all leds as outputs
GPIO.setup(wackLed1, GPIO.OUT)
GPIO.setup(wackLed2, GPIO.OUT)
GPIO.setup(wackLed3, GPIO.OUT)
GPIO.setup(wackLed4, GPIO.OUT)
GPIO.setup(wackLed5, GPIO.OUT)
GPIO.setup(elWire, GPIO.OUT)
GPIO.setup(roomLed, GPIO.OUT)



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                           FUNCTIONS                                   #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#



#################################
#         BUTTON PRESS          #
#################################
# gets called whenever there is a change in the disable/enable button
# detects rising or falling edge and records the duration of the press
# if it is greater than the disable duration, then exit flag is up and routine ends
# this is ignored if the alarm is latched because an alarm is ongoing
def disableBt_callback(channel):
  global buttRisingTime, buttFallingTime, buttDuration, disableTimme, prevBttnState
  buttValue = GPIO.input(channel)
  
  #if an alarm is ongoing then block
  if disableBtLatch:
    # after button is depressed count time
    if buttValue and prevBttnState:
      prevBttnState   = False
      buttFallingTime = time.time()
      buttDuration    = (buttFallingTime - buttRisingTime) if buttRisingTime is not None else None

      print "Detected edge {} duration {}".format(buttValue, buttDuration)

      if buttDuration > disableTime:
        exitFlag      = True
        print "Disableing process"
      else:
        print "press too short"
      
      #reset durations
      buttFallingTime = None
      buttDuration    = None
      buttRisingTime  = None
    
    # button is first pressed
    else:
      prevBttnState   = True
      buttFallingTime = None
      buttDuration    = None
      buttRisingTime  = time.time()

 #-----------------------------------------------#

# called when any wack button is pressed
def wack_callback(wackBt):
  global targetWack targetLed pressedWack wrongWack

  pressedWack = True

  if wackBt == targetWack:
    wrongWack = False
  else:
    wrongWack = True

  GPIO.output(targetLed, GPIO.HIGH)
 #-----------------------------------------------#

# called when any wack button is pressed
def timer_callback(timerBt):
  global targetWack targetLed pressedWack wrongWack

  pressedWack = True

  if wackBt == targetWack:
    wrongWack = False
  else:
    wrongWack = True

  GPIO.output(targetLed, GPIO.HIGH)
 #-----------------------------------------------#

#################################
#       VOLUME CONTROLS         #
#################################

# increases volume by sending a character command to mplayer
# 0 is mplayer's command to increase
def increase_volume():
  global volume, player, maxVol
  if (volume < maxVol):
    volume = volume + volumeStep
    print "Increasing volume to {}".format(volume)
    player.stdin.write('0')
    player.stdin.flush()

# decreases volume by sending a character command to mplayer
# 9 is mplayer's command to decrease
def decrease_volume():
  global volume, player, minVol
  if (volume > minVol):
    volume = volume - volumeStep
    print "Decreasing volume to {}".format(volume)
    player.stdin.write('9')
    player.stdin.flush()


#################################
#         GET BS DATA           #
#################################

def getbsdata():
  global rawImport, bsValue, bsTrend, bsDrop, bsData, bsTime

  rawImport = subprocess.call(["wget", "-O", "log", " https://wakeaboo.herokuapp.com/api/v1/entries/?token=raspi-97846cb04ad59b51"])
  
  #cast date and correct for timezone bug
  #TODO -- test separatelly
  timeStr = rawImport[12:20]

  #TODO -- if cant parse, access tthen no data
  if bsData
    bsTime  = datetime.strptime(timeStr, '%Y-%m-%dT%H:%M:%S')
    bsTime  = bsTime - timedelta(hours=5) 

    # if data is older than X min, no data
    if time.time()-timedelta(minutes=noDataTh) > bsTime:
      bsData = False
    else:
      bsData = True
    
    #cast bs
    #TODO -- this does not work, need to find tabs
    val = rawImport
    bsValue = int(val,base=10)
    
    #cast trend and drop
    trend = rawImport

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
    else trend == "DoubleDown":
      bsTrend = 5
      bsDrop  = 2
    
    rawImport = None

#################################
#          INTERRUPTS           #
#################################

GPIO.add_event_detect(disableBt, GPIO.BOTH, callback=disableBt_callback, bouncetime=100)

GPIO.add_event_detect(wackBt1, GPIO.RISING, callback=wack_callback, bouncetime=100)
GPIO.add_event_detect(wackBt2, GPIO.RISING, callback=wack_callback, bouncetime=100)
GPIO.add_event_detect(wackBt3, GPIO.RISING, callback=wack_callback, bouncetime=100)
GPIO.add_event_detect(wackBt4, GPIO.RISING, callback=wack_callback, bouncetime=100)
GPIO.add_event_detect(wackBt5, GPIO.RISING, callback=wack_callback, bouncetime=100)

GPIO.add_event_detect(timer15, GPIO.RISING, callback=timer_callback, bouncetime=100)
GPIO.add_event_detect(timer90, GPIO.RISING, callback=timer_callback, bouncetime=100)


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                             MAIN                                      #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

# initialize mplayer with prefered condigurations and introduce a delay to allow it to boot correctly
# kill the subprocess after. This is a workaround to allow mplayer to actually start volume at the command sent
# otherwise it actually does not.
alarm = subprocess.Popen(["mplayer", "-volume", str(volume), "-really-quiet", "/home/eleven/Alarms/Alarm03.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
time.sleep(5)
alarm.terminate()

# boot player once again with the prefered commands, and random song, and now it will init as indicated
# delay to allow player to finalize initialization
player = subprocess.Popen(["mplayer", "-volume", "-1", "-volstep", str(volumeStep), "-loop", "0", "-really-quiet", musicDir+songs[randSong]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
time.sleep(10)


while exitFlag==0:
  # increase volume periodially as per timeIncVol
  if (time.time()-lastTime >= timeIncVol):
    lastTime = time.time()
    increase_volume()

  # if user presses button, either short or long, decrease volume
  if(longPressWaiting or shortPressWaiting):
    longPressWaiting  = False
    shortPressWaiting = False
    decrease_volume()

    # if the exit sequence is found in the string of button presses, start to exit
    # kill the current song and start a new player with the end alarm sound
    if(exitSequence in buttSequence):            #exit, snoozed
      print "Exit Sequence Activated"
      player.terminate()
      exitFlag = 1
      alarm = subprocess.Popen(["mplayer", "-volume", "75", "-really-quiet", "/home/eleven/Alarms/Alarm03.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
      time.sleep(6)
      alarm.terminate()

  # after a long time, terminate the program
  if (time.time()-startTime > termLongTime):
    player.terminate()
    exitFlag = 1



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              EXIT                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
# first disable the shutdown routine and spotify
subprocess.call(["/etc/init.d/listen-for-shutdown.sh", "start"])
#TODO -- disable spotify

#EOF#
