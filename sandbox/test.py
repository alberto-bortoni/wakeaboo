#! /usr/bin/python3


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import os
import time
import subprocess
from subprocess import PIPE, STDOUT
#import shlex
from time import sleep
import RPi.GPIO as GPIO
#from random import *
from datetime import datetime
from datetime import timedelta
#import re
import board
from adafruit_ht16k33.matrix import Matrix8x8
from adafruit_ht16k33.matrix import MatrixBackpack16x8
import matrixDisplay as mat
import initPiState
import config as cfg
import sys

#################################
#            STARTUP            #
#################################
cfg.init()
initPiState.initPi()

mat.clear8Mat()
mat.clear16Mat()


exitFlag = False

#################################
#          INTERRUPTS           #
#################################

def end_callback(chan):
  sys.exit()
  exitFlag = True


GPIO.add_event_detect(cfg.pinPowerBt, GPIO.FALLING, callback=end_callback, bouncetime=70)

#################################
#             LOOP              #
#################################
while True:
  if exitFlag:
    sys.exit()

  mat.dispTime()

#  for i in range(0,50):
#    mat.print16Bar(50, i) 
#    time.sleep(1)

  time.sleep(1)
