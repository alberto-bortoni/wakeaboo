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
import settings as st

#################################
#          VARIABLESS           #
#################################
i2c = board.I2C()
disp16 = MatrixBackpack16x8(i2c, address=0x71)
disp16.brightness = 0.01
disp8 = Matrix8x8(i2c, address=0x70)
disp8.brightness = 0.1



#################################
#        BASE FUNCTIONS         #
#################################

#this only prints on the character area 16x7
def print16Mat():
  for r in range(0,7):
    for c in range (0,16):
      disp16[c,r] = np.matrix(st.ledmat)[r,c]
#-----------------------------------------------#

def fill16Mat(fill):
  for r in range(0,7):
    for c in range (0,16):
      disp16[c,r]    = 0
      st.ledmat[r,c] = 0
#-----------------------------------------------#

def clear16Mat():
  disp16.fill(0)
  st.ledmat = np.zeros((8,16))
#-----------------------------------------------#

#this only fills/emties the timer area 16x1
def fill16Bar(fill):
  r = 7
  for c in range (0,16):
    disp16[c,r]    = fill
    st.ledmat[r,c] = fill
#-----------------------------------------------#

def print8Mat():
  for r in range(0,8):
    for c in range (0,8):
      disp8[c,r] = np.matrix(st.arrmat)[r,c]
#-----------------------------------------------#

def clear8Mat():
  disp8.fill(0)
  st.arrmat = np.zeros((8,8))
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

def catTimeArr():
  colon   = [[0,0],[0,0],[1,0],[0,0],[1,0],[0,0],[0,0]]
  timenow = datetime.now()
  hr1 = timenow.hour//10
  hr2 = timenow.hour%10
  mi1 = timenow.minute//10
  mi2 = timenow.minute%10
  
  if hr1 == 0:
    st.ledmat[0:7, 0: 3] = numSmall(10)
  else:
    st.ledmat[0:7, 0: 3] = numSmall(hr1)
  
  st.ledmat[0:7, 4: 7]   = numSmall(hr2)
  st.ledmat[0:7, 7: 9]   = colon
  
  if mi1 == 0:
    st.ledmat[0:7, 9:12] = numSmall(10) 
  else:
    st.ledmat[0:7, 9:12] = numSmall(mi1) 
  
  st.ledmat[0:7,13:16]   = numSmall(mi2)
#-----------------------------------------------#

def catBsArr(bs):
  hun = bs//100
  ten = (bs%100)//10
  uni = bs%10

  if hun == 0:
    st.ledmat[0:7, 1: 5] = numBig(10)
  else:
    st.ledmat[0:7, 1: 5] = numBig(hun)

  st.ledmat[0:7, 6:10]   = numBig(ten)
  st.ledmat[0:7,11:15]   = numBig(uni)
#-----------------------------------------------#

#this only prints on the timer area 16x1
#it will print a prop ammout of dots given the
#size of total and lapsed
def print16Bar(tot, lap):
  if tot == lap:
    tmp = 16
  else:
    tmp = flo(17*lap/tot)
   
  r = 7
  print(tmp)
  if tmp == 0:
    fill16Bar(1)
  else:
    for c in range(0,tmp):
      disp16[c,r]    = 0
      st.ledmat[r,c] = 0
#-----------------------------------------------#

def printArr()
  if st.bsTrend == "DoubleUp":
    arrows()
    bsTrend = 1
    bsDrop  = 2
  elif st.bsTrend == "SingleUp":
    bsTrend = 1
    bsDrop  = 1
  elif st.bsTrend == "FortyFiveUp":
    bsTrend = 2
    bsDrop  = 0
  elif st.bsTrend == "Flat":
    bsTrend = 3
    bsDrop  = 0
  elif st.bsTrend == "FortyFiveDown":
    bsTrend = 4
    bsDrop  = 0
  elif st.bsTrend == "SingleDown":
    bsTrend = 5
    bsDrop  = 1
  elif st.bsTrend == "DoubleDown":
    bsTrend = 5
    bsDrop  = 2
  else:

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
  elif direc == 7:
    return np.array([[0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [1,0,1,0,0,1,0,1],
                     [0,1,1,1,1,1,1,0],
                     [0,0,1,0,0,1,0,0]])
  elif direc == 7:
    return np.array([[0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [0,0,1,0,0,1,0,0],
                     [1,0,1,0,0,1,0,1],
                     [0,1,1,1,1,1,1,0],
                     [0,0,1,0,0,1,0,0]])
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
