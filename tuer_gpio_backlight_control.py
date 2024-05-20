#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import os

pinNr = 19


GPIO.setmode(GPIO.BOARD)

GPIO.setup(pinNr, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# screensaver temporär auf 20s einstellen:
os.system("xset s 20")
os.system("xset dpms 20 20 20")

input_prev_state = GPIO.input(pinNr)

while True:
    input_value = GPIO.input(pinNr)

    if input_value == False and input_prev_state == True:
        # print("Taster gedrueckt")

        # screensaver temporär auf 20s einstellen:
        # xset s 20
        # xset dpms 20 20 20

        os.system("xset -display :0.0 dpms force on")

    
    input_prev_state = input_value

    time.sleep(0.1)


# Alternative ohne 'dpms energiesparmodus':
# Braucht root (sudo)
# with open("/sys/class/backlight/10-0045/bl_power", "w") as f:
# 	f.write("0")
