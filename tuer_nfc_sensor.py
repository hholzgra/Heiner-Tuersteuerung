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
log = logging.getLogger("NFC-Sensor")
log.setLevel(logging.INFO)

# Logging ins SystemD Journal wenn wir als service laufen
if 'INVOCATION_ID' in os.environ:
    from systemd.journal import JournalHandler
    log.addHandler(JournalHandler())

settings = Settings()

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
        # print('ON_1...')
        log.info("Relais angezogen")
        # journal.write("NFC-Sensor: Relais angezogen")
        self.DEVICE_REG_DATA &= ~(0x1 << 0)
        bus.write_byte_data(
            self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA
        )

    def OFF_1(self):
        # print('OFF_1...')
        log.info("Relais abgefallen")
        # journal.write("NFC-Sensor: Relais abgefallen")
        self.DEVICE_REG_DATA |= 0x1 << 0
        bus.write_byte_data(
            self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA
        )


# Erstelle ein "Contactless Frontend" (clf)
clf = nfc.ContactlessFrontend()


if __name__ == "__main__":

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

        # if tag.is_present is True:
        #    print("NFC-Reader: Tag gefunden und Tuer geoeffnet")

        # Zeige Seriennummer an
        seriennummer = binascii.hexlify(tag.identifier).decode("UTF-8")
        # print(seriennummer)
        log.info("Kartennummer: " + str(seriennummer))
        #        if seriennummer == "bc75ed67" or \  # 1
        #            seriennummer == "ea0388be" or \ # 2
        #            seriennummer == "c7ecfeef" or \ # 3
        #            seriennummer == "a3703b1c" or \ #4
        #            seriennummer == "6c961f31" or \ #5
        #            seriennummer == "760f4000" or \ #6
        #            seriennummer == "7a846f9c" or \ #7
        #            seriennummer == "07f406f0" or \ #8
        #            seriennummer == "772006f0" or \ #9
        #            seriennummer == "97e106f0" or \ #10
        #            seriennummer == "379cfaef" or \ #11
        #            seriennummer == "f74cf7ef" or \ #12
        #            seriennummer == "077901f0" or \ #13
        #            seriennummer == "d7c304f0" or \ #14
        #            seriennummer == "0aa4bfd3" or \ #15
        #            seriennummer == "6a88bfd3": #16

        if (
            seriennummer == "bc75ed67"
            or seriennummer == "ea0388be"
            or seriennummer == "c7ecfeef"
            or seriennummer == "a3703b1c"
            or seriennummer == "6c961f31"
            or seriennummer == "760f4000"
            or seriennummer == "7a846f9c"
            or seriennummer == "07f406f0"
            or seriennummer == "772006f0"
            or seriennummer == "97e106f0"
            or seriennummer == "379cfaef"
            or seriennummer == "f74cf7ef"
            or seriennummer == "077901f0"
            or seriennummer == "d7c304f0"
            or seriennummer == "0aa4bfd3"
            or seriennummer == "6a88bfd3"
        ):
            # print("NFC-Reader: Richtige Karte! Tuer geoeffnet.")
            log.info("Richtige Karte! Tuer geoeffnet.")
            # journal.write("NFC-Sensor: Richtige Karte! Tuer geoeffnet.")
            # Hier Tuer oeffnen
            relay.ON_1()
            time.sleep(2)
            relay.OFF_1()

            Telegram.bot_notification("Tür wurde mit Karte geöffnet.")

        else:
            # print("NFC-Reader: Falsche Karte erkannt!")
            log.info("Falsche Karte erkannt!")
            # journal.write("NFC-Sensor: Falsche Karte erkannt!")
            relay.OFF_1()
