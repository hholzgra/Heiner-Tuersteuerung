#! /bin/env python3

# TODO das alles hier gehört eigentlich in die Hauptanwendung
#      der Näherungs-Pin kann auch dort in der GUI-Event-Schleife
#      über den "after()" Callback abgefragt werden

import RPi.GPIO as GPIO
import time
import os

from Settings import Settings
settings = Settings()

# Logging initialisieren
logging.basicConfig()
log = logging.getLogger("Tuerbeleuchtung")
log.setLevel(logging.INFO)

pins = settings.get("pins")
pinNr = pins["backlight"] or 19

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pinNr, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Achtung dies Setup wird auch vom gui gemacht (Fake Blackscreen)

screen = Settings.get("screen")
timeout = screen["timeout"]

# screensaver temporär auf timeout einstellen:
os.system("xset s %d" % timeout)
os.system("xset dpms %d %d %d" % (timeout, timeout, timeout))

input_prev_state = GPIO.input(pinNr)

while True:
    input_value = GPIO.input(pinNr)

    if input_value == False and input_prev_state == True:
        log.info("Taster / Sensor ausgelöst, Bildschirm hell")
        os.system("xset -display :0.0 dpms force on")
    
    input_prev_state = input_value

    time.sleep(0.1)


# Alternative ohne 'dpms energiesparmodus':
# Braucht root (sudo)
# with open("/sys/class/backlight/10-0045/bl_power", "w") as f:
# 	f.write("0")
