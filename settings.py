#! /usr/bin/python3


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import os
from datetime import datetime
from datetime import timedelta
import board
import numpy as np

def init():
  #led matrices array handler
  global ledmat, arrmat
  ledmat = np.zeros((8,16))
  arrmat = np.zeros((8,8))

  #player routine
  global alarmproc

  #CGM data
  global bsVal, bsTrend, cgmErr
  bsVal    = 0
  bsTrend  = "nan" 
