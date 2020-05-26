#!/usr/bin/python3

#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
#                              HEAD                                     #
#|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||#
import os
import board
import RPi.GPIO as GPIO
import matrixDisplay as mat
import config as cfg

def initPi():
  #set gpio mode
  GPIO.setmode(GPIO.BCM)

  #state of wack buttons/leds
  GPIO.setup(cfg.pinWackBt1, GPIO.IN)
  GPIO.setup(cfg.pinWackBt2, GPIO.IN)
  GPIO.setup(cfg.pinWackBt3, GPIO.IN)
  GPIO.setup(cfg.pinWackLed1, GPIO.OUT, initial=0)
  GPIO.setup(cfg.pinWackLed2, GPIO.OUT, initial=0)
  GPIO.setup(cfg.pinWackLed3, GPIO.OUT, initial=0)

  #state of timer buttons
  GPIO.setup(cfg.pinTimerBt1, GPIO.IN)
  GPIO.setup(cfg.pinTimerBt2, GPIO.IN)

  #state of power button
  GPIO.setup(cfg.pinPowerBt, GPIO.IN)
  GPIO.setup(cfg.pinPowerLed, GPIO.OUT, initial=0)

  #highpower led
  GPIO.setup(cfg.pinHighPowerLed, GPIO.OUT, initial=0)

  #turn off led matrices
  mat.clear8Mat()
  mat.clear16Mat()

#if excecuted as script
if __name__=='__main__':
  initPi()

#EOF#
