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
import re
from random import random


# first disable the shutdown routine and spotify
subprocess.call(["/etc/init.d/listen-for-shutdown.sh", "stop"])
# enable print
enablePrint = True

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
bsVal     = 0  # mg/dl
bsTrend   = "nan"  # 1:90up 2:45up 3:flat 4:45down 5:90down
bsDrop    = 0  # 0:noSpeed 1:oneArrow 2:twoArrow
cmgErr    = 0
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

  pressedWack  = True
  pendingPress = True
  
  if wackBt == targetWack and totAckPress > 0 and
     (highBsStateFlag or lowBsStateFlag or uLowBsStateFlag):
    wrongWack    = False #TODO-- this is prob nothing
    totAckPress -= 1
    decrease_volume()
  else:
    wrongWack = True
    increase_volume()
    if highBsStateFlag:
      totAckPress = highAckPress
    elif lowBsStateFlag:
      totAckPress = lowAckPress
    elif ulowBsStateFlag:
      totAckPress = uLowAckPress
    elif errStateFlag:
      totAckPress = errAckPress
    elif dropStateFlag:
      totAckPress = droppingAckPress
    elif riseStateFlag:
      totAckPress = risingAckPress

  GPIO.output(targetLed, GPIO.HIGH)
 #-----------------------------------------------#

# called when any timer button is pressed
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
#           DISPLAY             #
#################################
def updateDisplay():
  #no error; display bs
  if bsDataErr == 0:



  #display error msg
  else:


 #-----------------------------------------------#



#################################
#         GET BS DATA           #
#################################

def getbsData():
  global rawImport, bsValue, bsTrend, bsDrop, bsDataAv, bsTime

  #cast date and correct for timezone bug
  rawImport  =  subprocess.check_output(["wget","-q","-O","-","https://wakeaboo.herokuapp.com/api/v1/entries/current/?token=raspi-97846cb04ad59b51"])
  castTab    = re.compile("[^\t]+")
  rawParts   = castTab.findall(rawImport)

  #TODO -- if cant parse, access tthen no data
  #if bsDataAv
  timeStr = rawParts[0][1:20]
  bsTime  = datetime.strptime(timeStr, '%Y-%m-%dT%H:%M:%S')
  #TODO -- fix with timezone, otherwise issues with DTS
  bsTime  = bsTime - timedelta(hours=5)

  # if data is older than X min, no data
  if datetime.now()-timedelta(minutes=noDataTh) > bsTime:
    bsDataAv = False
  else:
    bsDataAv = True

  #cast bs
  tval    = rawParts[2]
  bsValue = int(tval,base=10)

  #cast trend and drop
  trend = rawParts[3][1:-1]

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
  elif trend == "DoubleDown":
    bsTrend = 5
    bsDrop  = 2

  rawImport = None

  print "time {}".format(bsTime)
  print "data {}".format(bsDataAv)
  print "value {}".format(bsValue)
  print "trendT {}".format(trend)
  print "trend {}".format(bsTrend)
  print "drop {}".format(bsDrop)
 #-----------------------------------------------#

 

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


#################################
#             LOOP              #
#################################

while exitFlag == 0:

  #-----------------------------------------------#
  #get BS values
  if datetime.now()-timedelta(seconds=bsServiceLoop) > lastBsLoop:
    getbsData()
    lastBsLoop = datetime.now()

  #-----------------------------------------------#
  #update Display if new data avail
  if bsDataAv:
    updateDisplay()
    bsDataAv = False

  #-----------------------------------------------#
  #check for alarms
  #type: 1urHigh 2high 3low 4urLow 5noData 6drop 7rise
  #high for the first time
  if (bsValue>=highBs or highBsSateFlag) and not alarmPrimedFlag:
    alarmTriggerTime = datetime.now()
    bsValueTrigger   = bsValue
    highBsStateFlag  = True
    alarmTriggerFlag = True
    alarmPrimedFlag  = True
    pendingPress     = True
    totAckPress      = highAckPress
    triggerAlarm(2)
  #if it rises more than the threshold
  elif alarmPrimedFlag and highBsStateFlag and bsValueTrigger+highStBs>=bsValue 
       and not alarmTriggerFlag:
    alarmTriggerTime = datetime.now()
    bsValueTrigger   = bsValue
    highBsStateFlag  = True
    alarmTriggerFlag = True
    pendingPress     = True
    totAckPress      = highAckPress
    triggerAlarm(2)
  #if time has passed but bs has not decreased by step
  elif alarmPrimedFlag and highBsStateFlag and highBsStateFlag 
       and alarmTriggerTime+timedelta(minutes=highTime)>datetime.now() 
       and bsValueTrigger-highStBs <= bsValue and not alarmTriggerFlag:
    alarmTriggerTime = datetime.now()
    bsValueTrigger   = bsValue
    highBsStateFlag  = True
    alarmTriggerFlag = True
    totAckPress      = highAckPress
    pendingPress     = True
    triggerAlarm(2)
  #if it has dropped enough
  elif highBsStateFlag and bsValueTrigger-highStBs > bsValue:
    highBsStateFlag  = False
    alarmTriggerFlag = False
    alarmPrimedFlag  = False
    pendingPress     = False


  #low
  if (bsValue<=lowBs and bsValue>urLowBs) or lowBsStateFlag:
    triggerAlarm(3)
    lowBsStateFlag = True

  #urgetnt low
  if bsValue<=urLowBs or uLowBsStateFlag:
    triggerAlarm(4)
    uLowBsStateFlag = True 

  #data error 
  if bsDataErr != 0: 
    triggerAlarm(5)  

  #dropping
  if bsValue<highBs and bsDrop == 2: 
    triggerAlarm(6)  

  #rising
  if bsValue>lowBs and bsDrop == 2:
    triggerAlarm(7)  

  #-----------------------------------------------#
  #volume increase
  if alarmTriggerFlag and datetime.now()>lastVolInc+timedelta(seconds=incvolServ):
    lastVolInc = datetime.now()
    increase_volume()

 
  #-----------------------------------------------#
  #acknowledge alarm
  if alarmTriggerFlag and totAckPress > 0 and pendingPress:
    pendingPress = False
    tmp = random.randint(0,4)
    targetWack   = wacks[tmp]
    targetLed    = targetWack
    GPIO.output(targetLed, GPIO.LOW)
  elif alarmTriggerFlag and totAckPress == 0:
    alarmTriggerFlag = False
    alarmPrimedFlag  = True #TODO -- belongs here?
    alarm.terminate()
    GPIO.output(targetLed, GPIO.LOW)
    

  #-----------------------------------------------#



#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              EXIT                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
# first disable the shutdown routine and spotify
subprocess.call(["/etc/init.d/listen-for-shutdown.sh", "start"])
#TODO -- disable spotify

#EOF#
