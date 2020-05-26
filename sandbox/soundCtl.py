#! /usr/bin/python3

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import mpylayer
import os
import time
import subprocess
from subprocess import PIPE, STDOUT
from time import sleep


#################################
#          VARIABLES            #
#################################

#alarm
alarm = None

#alarm variables
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


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                           FUNCTIONS                                   #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#


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
  global alarm

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

    alarm = subprocess.Popen(["mplayer", "-volume", "-1", "-volstep",
                          str(volumeStep), "-loop", "0", "-really-quiet",
                          alarmSound, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True)

    # delay to allow player to finalize initialization
    time.sleep(10)
 #-----------------------------------------------#


# decreases volume by sending a character command to mplayer
# 9 is mplayer's command to decrease
def killAlarm():
  global alarm
  alarm.terminate()
  alarm = None
 #-----------------------------------------------#

#EOF#
