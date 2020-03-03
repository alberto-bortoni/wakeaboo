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
# using hardware GPIO13 lisen for a 5 sec press to power button
# then shutdown system
GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
  falling = GPIO.wait_for_edge(13, GPIO.FALLING)
  time.sleep(0.2)

  if falling is not None:
    rising = GPIO.wait_for_edge(13, GPIO.RISING, timeout=5000)
    if rising is None:
      time.sleep(5)
      subprocess.call(['shutdown', '-h', 'now'], shell=False)
