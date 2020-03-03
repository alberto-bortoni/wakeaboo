#!/usr/bin/env python

import mpylayer
import os
import time
import subprocess
from subprocess import PIPE, STDOUT
import shlex
from time import sleep
import RPi.GPIO as GPIO

# this file belongs in /usr/local/bin/
# using hardware GPIO5 enables alarm clock until deactivated
# by user or (usually) by crontab at a spesific time
# user needs to press for 3 sec.
# using GPIO6 for led indicator
butt = 5;
led  = 6;

GPIO.setmode(GPIO.BCM)
GPIO.setup(butt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(led, GPIO.OUT)

# trun on led
GPIO.output(led, GPIO.HIGH)

# until a user press is detected
while True:
  falling = GPIO.wait_for_edge(butt, GPIO.FALLING)
  time.sleep(0.2)

  if falling is not None:
    rising = GPIO.wait_for_edge(butt, GPIO.RISING, timeout=5000)
    if rising is None:
      GPIO.output(led, GPIO.LOW)
      time.sleep(2)
      subprocess.call(['python', '~/wakeaboo/alarm-main.py'], shell=False)
      time.sleep(2)
      GPIO.output(led, GPIO.HIGH)
