#! /bin/env python3

import nfc
import binascii
import signal
import sys
import smbus
import time
import logging
import os
from systemd.journal import JournalHandler
import requests

from Settings import Settings
import Telegram

# systemd logger
logging.basicConfig()
log = logging.getLogger("NFC-Sensor")
log.setLevel(logging.INFO)

# Logging ins SystemD Journal wenn wir als service laufen
if 'INVOCATION_ID' in os.environ:
    from systemd.journal import JournalHandler
    log.addHandler(JournalHandler())

# Relay Karte
bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)


class Relay:
    global bus

    def __init__(self):
        self.DEVICE_ADDRESS = (
            0x20  # 7 bit address (will be left shifted to add the read write bit)
        )
        self.DEVICE_REG_MODE1 = 0x06
        self.DEVICE_REG_DATA = 0xFF
        bus.write_byte_data(
            self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA
        )

    def ON_1(self):
        log.debug("NFC-Sensor: Relais angezogen")
        self.DEVICE_REG_DATA &= ~(0x1 << 0)
        bus.write_byte_data(
            self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA
        )

    def OFF_1(self):
        log.debug("NFC-Sensor: Relais abgefallen")
        self.DEVICE_REG_DATA |= 0x1 << 0
        bus.write_byte_data(
            self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA
        )


# Erstelle ein "Contactless Frontend" (clf)
clf = nfc.ContactlessFrontend()


if __name__ == "__main__":
    settings = Settings()
    nfc = settings.get("nfc")

    relay = Relay()

    # Called on process interruption. Set all pins to "Input" default mode.
    def endProcess(signalnum=None, handler=None):
        relay.ALLOFF()
        clf.close()
        sys.exit()

    signal.signal(signal.SIGINT, endProcess)

    while True:
        # ct = input("input: ")

        # Öffne das NFC Modul an der seriellen Schnittstelle
        assert clf.open("tty:S0:pn532") is True

        # Stelle Verbindung zu einem NFC Tag her
        tag = clf.connect(rdwr={"on-connect": lambda tag: False})

        # Zeige Seriennummer an
        seriennummer = binascii.hexlify(tag.identifier).decode("UTF-8")
        log.info("Kartennummer: " + str(seriennummer))

        # Prüfe Seriennummer
        if seriennummer in nfc["tokens"]:
            log.info("Richtige Karte! Tuer geoeffnet.")
            # Hier Tuer oeffnen
            relay.ON_1()
            time.sleep(2)
            relay.OFF_1()

            Telegram.bot_notification("Tür wurde mit Karte geöffnet.")

        else:
            log.info("Falsche Karte erkannt!")
            relay.OFF_1()
