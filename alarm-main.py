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

# first disable the shutdown routine
subprocess.call(["/etc/init.d/listen-for-shutdown.sh", "stop"])

#################################
#          VARIABLES            #
#################################

subprocess.call(["wget", "-O", "log", " https://wakeaboo.herokuapp.com/api/v1/entries/?token=raspi-97846cb04ad59b51"])

#times in seconds
longPressTime     = 3
termLongTime      = 600
startTime         = time.time()
lastTime          = time.time()
buttRisingTime    = None
buttFallingTime   = None
buttDuration      = None
longPressWaiting  = False
shortPressWaiting = False
disableTime       = 3

#player volume
volume      = 10
volumeStep  = 2
maxVol      = 110
minVol      = 30
timeIncVol  = 1

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
bsValue   = 0 # mg/dl
bsTrend   = 0 # 1:horz 2:45up 3:90up 4:45down 5:90down
bsDrop    = 0 # 0:noSpeed 1:oneArrow 2:twoArrow

#aduio related stuff
alarmHigh   = "/home/boo/wakeaboo/audio/"
alarmHighUr = "/home/boo/wakeaboo/audio/"
alarmLow    = "/home/boo/wakeaboo/audio/"
alarmLowUr  = "/home/boo/wakeaboo/audio/"
alarmNoData = "/home/boo/wakeaboo/audio/"
alarmDrop   = "/home/boo/wakeaboo/audio/"
alarmRaise  = "/home/boo/wakeaboo/audio/"

songs    = os.listdir(musicDir)
songsNum = len(songs)
randSong = randint(1, songsNum)-1

#button press sequence for shutting off alarm
exitSequence    = 'sslssl'
exitFlag        = 0
snooze          = 0
numLongPresses  = 0
numShortPresses = 0
buttSequence    = "" # empty sequence
prevBttnState   = False

# target buttons
targetWack = 0
targetLed  = 0


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
elWire      =  4 #pin  7




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



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                           FUNCTIONS                                   #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#

# gets called whenever there is a change in the button input
# detects rising or falling edge and records the duration of the press
# categorizes it as a short or long press according to pre determiend values above
def butt_callback(channel):
  global buttSequence, buttRisingTime, buttFallingTime, buttDuration, longPressTime, longPressWaiting, shortPressWaiting, numLongPresses, numShortPresses, prevBttnState
  buttValue = GPIO.input(channel)

  if buttValue and prevBttnState:
    prevBttnState   = False
    buttFallingTime = time.time()
    buttDuration    = (buttFallingTime - buttRisingTime) if buttRisingTime is not None else None

    print "Detected edge {} on channel {} at {} duration {}".format(buttValue, channel, buttRisingTime, buttDuration)

    if buttDuration > longPressTime:
      longPressWaiting   = True
      numLongPresses    += 1
      buttSequence      += 'l'
      print "LONG PRESS {}".format(numLongPresses)

    elif buttDuration is not None:
      shortPressWaiting  = True
      numShortPresses   += 1
      buttSequence      += 's'
      print "SHORT PRESS {}".format(numShortPresses)


    buttFallingTime = None
    buttDuration    = None
    buttRisingTime  = None
    print 'Sequence: {}'.format(buttSequence)

  else:
    prevBttnState   = True
    buttFallingTime = None
    buttDuration    = None
    buttRisingTime  = time.time()

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
#          INTERRUPTS           #
#################################

GPIO.add_event_detect(disableBt, GPIO.BOTH, callback=disableBt_callback, bouncetime=100)

GPIO.add_event_detect(wackBt1, GPIO.BOTH, callback=wackBt1_callback, bouncetime=100)
GPIO.add_event_detect(wackBt2, GPIO.BOTH, callback=wackBt2_callback, bouncetime=100)
GPIO.add_event_detect(wackBt3, GPIO.BOTH, callback=wackBt3_callback, bouncetime=100)
GPIO.add_event_detect(wackBt4, GPIO.BOTH, callback=wackBt4_callback, bouncetime=100)
GPIO.add_event_detect(wackBt5, GPIO.BOTH, callback=wackBt5_callback, bouncetime=100)

GPIO.add_event_detect(timer15, GPIO.BOTH, callback=butt_callback, bouncetime=100)
GPIO.add_event_detect(timer90, GPIO.BOTH, callback=butt_callback, bouncetime=100)


GPIO.setup(disableBt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(wackBt5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(timer15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(timer90, GPIO.IN, pull_up_down=GPIO.PUD_UP)



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


# first disable the shutdown routine
subprocess.call(["/etc/init.d/listen-for-shutdown.sh", "start"])

#EOF#
