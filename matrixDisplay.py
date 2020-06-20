#! /usr/bin/python3

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import os
import time
from time import sleep
import RPi.GPIO as GPIO
from datetime import datetime
from datetime import timedelta
import board
from adafruit_ht16k33.matrix import Matrix8x8
from adafruit_ht16k33.matrix import MatrixBackpack16x8
import numpy as np
from math import floor as flo
import config as cfg

#################################
#          VARIABLESS           #
#################################
i2c = board.I2C()
disp16 = MatrixBackpack16x8(i2c, address=0x71)
disp16.blink_rate = 0
disp16.brightness = 0
disp8 = Matrix8x8(i2c, address=0x70)
disp8.blink_rate = 0
disp8.brightness = 0



#################################
#        BASE FUNCTIONS         #
#################################

#this only prints on the character area 16x7
def print16Mat():
  for r in range(0,7):
    for c in range (0,16):
      disp16[c,r] = np.matrix(cfg.ledmat)[r,c]
#-----------------------------------------------#

#this only prints on the character area 16x7
def fill16Mat(fill):
  for r in range(0,7):
    for c in range (0,16):
      disp16[c,r]     = fill
      cfg.ledmat[r,c] = fill
#-----------------------------------------------#

#this only prints on the timer area 16x1
#it will print a prop ammout of dots given the
#size of total and lapsed
def print16Bar(tot, lap):
  if tot <= lap:
    tmp = 16
  else:
    tmp = flo(17*lap/tot)
   
  r = 7
  if tmp == 0:
    fill16Bar(1)
  else:
    for c in range(0,tmp):
      disp16[c,r]     = 0
      cfg.ledmat[r,c] = 0
#-----------------------------------------------#

#this only fills/emties the timer area 16x1
def fill16Bar(fill):
  r = 7
  for c in range (0,16):
    disp16[c,r]     = fill
    cfg.ledmat[r,c] = fill
#-----------------------------------------------#

def clear16Mat():
  disp16.fill(0)
  cfg.ledmat = np.zeros((8,16))
#-----------------------------------------------#

def print8Mat():
  for r in range(0,8):
    for c in range (0,8):
      disp8[c,r] = np.matrix(cfg.arrmat)[r,c]
#-----------------------------------------------#

def fill8Mat(fill):
  for r in range(0,8):
    for c in range (0,8):
      disp8[c,r]      = fill
      cfg.arrmat[r,c] = fill
#-----------------------------------------------#

def clear8Mat():
  disp8.fill(0)
  cfg.arrmat = np.zeros((8,8))
#-----------------------------------------------#



#################################
#          FUNCTIONS           #
#################################
def mkEmptyArr(size):
  if size == 16:
    return np.zeros((8,16))
  else:
    return np.zeros((8,8))
#-----------------------------------------------#

def dispTime():
  colon   = [[0,0],[0,0],[1,0],[0,0],[1,0],[0,0],[0,0]]
  timenow = datetime.now()
  hr1 = timenow.hour//10
  hr2 = timenow.hour%10
  mi1 = timenow.minute//10
  mi2 = timenow.minute%10

#  if hr1 == 0:
#    cfg.ledmat[0:7, 0: 3] = numSmall(10)
#  else:
#    cfg.ledmat[0:7, 0: 3] = numSmall(hr1)
  
  cfg.ledmat[0:7, 0: 3] = numSmall(hr1)
  cfg.ledmat[0:7, 4: 7]   = numSmall(hr2)
  cfg.ledmat[0:7, 7: 9]   = colon
  
#  if mi1 == 0:
#    cfg.ledmat[0:7, 9:12] = numSmall(10) 
#  else:
#    cfg.ledmat[0:7, 9:12] = numSmall(mi1) 
  
  cfg.ledmat[0:7, 9:12] = numSmall(mi1) 
  cfg.ledmat[0:7,13:16]   = numSmall(mi2)

  print16Mat()
#-----------------------------------------------#

def dispShd():
  clear16Mat()
  cfg.ledmat[0:7, 1: 5] = charBig("s")
  cfg.ledmat[0:7, 6:10] = charBig("h")
  cfg.ledmat[0:7,11:15] = charBig("d")
  print16Mat()
#-----------------------------------------------#

def dispGluc():
  clear16Mat()
  cfg.ledmat[0:7, 1: 5] = charBig("g")
  cfg.ledmat[0:7, 6:10] = charBig("l")
  cfg.ledmat[0:7,11:15] = charBig("u")
  print16Mat()
#-----------------------------------------------#

def dispNumber(numb):
  numb = flo(numb*10)
  hun = numb//100
  ten = (numb%100)//10
  uni = numb%10

  if hun == 0:
    cfg.ledmat[0:7, 1: 5] = numBig(10)
  else:
    cfg.ledmat[0:7, 1: 5] = numBig(hun)

  cfg.ledmat[0:7, 6:10]   = numBig(ten)
  cfg.ledmat[0:7,11:15]   = numBig(uni)
  cfg.ledmat[6,10]        = 1
  print16Mat()
#-----------------------------------------------#


def dispBsArr():
  hun = cfg.bsValue//100
  ten = (cfg.bsValue%100)//10
  uni = cfg.bsValue%10

  if hun == 0:
    cfg.ledmat[0:7, 1: 5] = numBig(10)
  else:
    cfg.ledmat[0:7, 1: 5] = numBig(hun)

  cfg.ledmat[0:7, 6:10]   = numBig(ten)
  cfg.ledmat[0:7,11:15]   = numBig(uni)
  print16Mat()
#-----------------------------------------------#


def printArrow():
  if cfg.bsTrend == "DoubleUp":
    cfg.arrmat = arrows(1)
  elif cfg.bsTrend == "SingleUp":
    cfg.arrmat = arrows(2)
  elif cfg.bsTrend == "FortyFiveUp":
    cfg.arrmat = arrows(3)
  elif cfg.bsTrend == "Flat":
    cfg.arrmat = arrows(4)
  elif cfg.bsTrend == "FortyFiveDown":
    cfg.arrmat = arrows(5)
  elif cfg.bsTrend == "SingleDown":
    cfg.arrmat = arrows(6)
  elif cfg.bsTrend == "DoubleDown":
    cfg.arrmat = arrows(7)
  elif cfg.bsTrend == "nan":
    cfg.arrmat = arrows(8)
  else:
    cfg.arrmat = arrows(0)
  #installed flipped to what originally thought
  cfg.arrmat = np.rot90(cfg.arrmat,2)
  print8Mat()
#-----------------------------------------------#


#################################
#            ARRAYS             #
#################################

def arrows(direc):
  if direc == 1:
    return np.array([[0,0,1,0,0,1,0,0],
                     [0,1,1,1,1,1,1,0],
                     [1,0,1,0,0,1,0,1],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0]])
  elif direc == 2:
    return np.array([[0,0,0,1,0,0,0,0],
                     [0,0,1,1,1,0,0,0],
                     [0,1,0,1,0,1,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,1,0,0,0,0]])
  elif direc == 3:
    return np.array([[0,0,0,0,0,0,0,0],
                     [0,0,0,1,1,1,1,0],
                     [0,0,0,0,0,1,1,0],
                     [0,0,0,0,1,0,1,0],
                     [0,0,0,1,0,0,1,0],
                     [0,0,1,0,0,0,0,0],
                     [0,1,0,0,0,0,0,0],
                     [1,0,0,0,0,0,0,0]])
  elif direc == 4:
    return np.array([[0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,1,0,0],
                     [0,0,0,0,0,0,1,0],
                     [1,1,1,1,1,1,1,1],
                     [0,0,0,0,0,0,1,0],
                     [0,0,0,0,0,1,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0]])
  elif direc == 5:
    return np.array([[1,0,0,0,0,0,0,0],
                     [0,1,0,0,0,0,0,0],
                     [0,0,1,0,0,0,0,0],
                     [0,0,0,1,0,0,1,0],
                     [0,0,0,0,1,0,1,0],
                     [0,0,0,0,0,1,1,0],
                     [0,0,0,1,1,1,1,0],
                     [0,0,0,0,0,0,0,0]])
  elif direc == 6:
    return np.array([[0,0,0,1,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,1,0,1,0,1,0,0],
                     [0,0,1,1,1,0,0,0],
                     [0,0,0,1,0,0,0,0]])
  elif direc == 7:
    return np.array([[0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [1,0,1,0,0,1,0,1],
                     [0,1,1,1,1,1,1,0],
                     [0,0,1,0,0,1,0,0]])
  elif direc == 8:
    return np.array([[0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,1,1,0,0,0],
                     [0,0,0,1,1,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0]])
  elif direc == 9:
    return np.array([[0,0,0,0,0,0,0,0],
                     [0,0,1,1,1,1,0,0],
                     [0,0,1,0,0,0,0,0],
                     [0,0,1,1,1,0,0,0],
                     [0,0,1,0,0,0,0,0],
                     [0,0,1,0,0,0,0,0],
                     [0,0,1,1,1,1,0,0],
                     [0,0,0,0,0,0,0,0]])
  elif direc == 0:
    return np.array([[0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0]])
#-----------------------------------------------#

def charBig(char):
  if char == "g":
    return np.array([[0,1,1,0],[1,0,0,1],
                     [1,0,0,0],[1,0,1,0],
                     [1,0,0,1],[1,0,0,1],
                     [0,1,1,0]])
  elif char == "l":
    return np.array([[1,0,0,0],[1,0,0,0],
                     [1,0,0,0],[1,0,0,0],
                     [1,0,0,0],[1,0,0,0],
                     [1,1,1,1]])
  elif char == "u":
    return np.array([[1,0,0,1],[1,0,0,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,1,1,1]])
  elif char == "s":
    return np.array([[1,1,1,1],[1,0,0,0],
                     [1,0,0,0],[0,1,1,0],
                     [0,0,0,1],[0,0,0,1],
                     [1,1,1,1]])
  elif char == "h":
    return np.array([[1,0,0,1],[1,0,0,1],
                     [1,0,0,1],[1,1,1,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,0,0,1]])
  elif char == "d":
    return np.array([[1,1,1,0],[1,0,0,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,1,1,0]])
  else:
    return np.array([[0,0,0,0],[0,0,0,0],
                     [0,0,0,0],[0,0,0,0],
                     [0,0,0,0],[0,0,0,0],
                     [0,0,0,0]])
#-----------------------------------------------#

def numBig(num):
  if num == 0:
    return np.array([[1,1,1,1],[1,0,0,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,1,1,1]])
  elif num == 1:
    return np.array([[0,1,1,0],[1,0,1,0],
                     [0,0,1,0],[0,0,1,0],
                     [0,0,1,0],[0,0,1,0],
                     [1,1,1,1]])
  elif num == 2:
    return np.array([[0,1,1,0],[1,0,0,1],
                     [1,0,0,1],[0,0,1,0],
                     [0,1,0,0],[1,0,0,0],
                     [1,1,1,1]])
  elif num == 3:
    return np.array([[0,1,1,0],[1,0,0,1],
                     [0,0,0,1],[0,0,1,0],
                     [0,0,0,1],[1,0,0,1],
                     [0,1,1,0]])
  elif num == 4:
    return np.array([[1,0,0,1],[1,0,0,1],
                     [1,0,0,1],[1,1,1,1],
                     [0,0,0,1],[0,0,0,1],
                     [0,0,0,1]])
  elif num == 5:
    return np.array([[1,1,1,1],[1,0,0,0],
                     [1,0,0,0],[1,1,1,1],
                     [0,0,0,1],[0,0,0,1],
                     [1,1,1,1]])
  elif num == 6:
    return np.array([[1,1,1,1],[1,0,0,0],
                     [1,0,0,0],[1,1,1,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,1,1,1]])
  elif num == 7:
    return np.array([[1,1,1,1],[0,0,0,1],
                     [0,0,0,1],[0,0,1,0],
                     [0,1,0,0],[1,0,0,0],
                     [1,0,0,0]])
  elif num == 8:
    return np.array([[1,1,1,1],[1,0,0,1],
                     [1,0,0,1],[1,1,1,1],
                     [1,0,0,1],[1,0,0,1],
                     [1,1,1,1]])
  elif num == 9:
    return np.array([[1,1,1,1],[1,0,0,1],
                     [1,0,0,1],[1,1,1,1],
                     [0,0,0,1],[0,0,0,1],
                     [0,0,0,1]])
  elif num == 10:
    return np.array([[0,0,0,0],[0,0,0,0],
                     [0,0,0,0],[0,0,0,0],
                     [0,0,0,0],[0,0,0,0],
                     [0,0,0,0]])
#-----------------------------------------------#

def numSmall(num):
  if num == 0:
    return np.array([[1,1,1],[1,0,1],
                     [1,0,1],[1,0,1],
                     [1,0,1],[1,0,1],
                     [1,1,1]])
  elif num == 1:
    return np.array([[0,1,0],[1,1,0],
                     [0,1,0],[0,1,0],
                     [0,1,0],[0,1,0],
                     [1,1,1]])
  elif num == 2:
    return np.array([[0,1,0],[1,0,1],
                     [0,0,1],[0,0,1],
                     [0,1,0],[1,0,0],
                     [1,1,1]])
  elif num == 3:
    return np.array([[0,1,0],[1,0,1],
                     [0,0,1],[0,1,0],
                     [0,0,1],[1,0,1],
                     [0,1,0]])
  elif num == 4:
    return np.array([[1,0,1],[1,0,1],
                     [1,0,1],[1,1,1],
                     [0,0,1],[0,0,1],
                     [0,0,1]])
  elif num == 5:
    return np.array([[1,1,1],[1,0,0],
                     [1,0,0],[1,1,1],
                     [0,0,1],[0,0,1],
                     [1,1,1]])
  elif num == 6:
    return np.array([[1,1,1],[1,0,0],
                     [1,0,0],[1,1,1],
                     [1,0,1],[1,0,1],
                     [1,1,1]])
  elif num == 7:
    return np.array([[1,1,1],[0,0,1],
                     [0,0,1],[0,1,0],
                     [0,1,0],[1,0,0],
                     [1,0,0]])
  elif num == 8:
    return np.array([[1,1,1],[1,0,1],
                     [1,0,1],[1,1,1],
                     [1,0,1],[1,0,1],
                     [1,1,1]])
  elif num == 9:
    return np.array([[1,1,1],[1,0,1],
                     [1,0,1],[1,1,1],
                     [0,0,1],[0,0,1],
                     [0,0,1]])
  elif num == 10:
    return np.array([[0,0,0],[0,0,0],
                     [0,0,0],[0,0,0],
                     [0,0,0],[0,0,0],
                     [0,0,0]])
#-----------------------------------------------#

#EOF
