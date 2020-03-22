#! /usr/bin/python3


#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import os
import time
#import subprocess
#from subprocess import PIPE, STDOUT
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
import numpy as np
import matrixDisplay as mat

while True:
  mat.clear8Mat()
  mat.clear16Mat()
  tmp = mat.mkEmptyArr(16)
  tmp = mat.catBsArr(tmp, 254)
  mat.print16Mat(tmp)
  for i in range(0,50):
    mat.print16Bar(tmp, 50, i) 
    time.sleep(1)
