import threading
import time
import platform
import logging

from Settings import Settings

settings = Settings()

# Logging initialisieren
log = logging.getLogger("Tuersteuerung")

if platform.uname().system == "Linux" and platform.uname().node == "raspberrypi":
    import RPi.GPIO as GPIO

class BeeperSteuerung(threading.Thread):

    DEFAULT_ANSTEUERZEIT_SEK = 0.5

    def __init__(self, stop_event: threading.Event, demo_modus=False) -> None:
        super().__init__()

        self.demo_modus = demo_modus
        self.stop_event = stop_event

        pins = settings.get("gpio")
        self.BeeperpinNr = pins["beeper"] or 15

        if not self.demo_modus:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.BeeperpinNr, GPIO.OUT)

        self.Timer = 0

    def run(self):

        while not self.stop_event.is_set():

            time.sleep(0.01)
            if self.Timer > 0:
                self.Timer = self.Timer - 1  # der Timerwert entspricht 10ms Raster
                if self.Timer == 0:
                    # Timer hat Null erreicht, Relais abschalten
                    self._BeeperOFF()

    def TriggerBeeper(self, Ansteuerzeit_Sek=DEFAULT_ANSTEUERZEIT_SEK) -> None:
        """Schaltet ein Relais ein und zieht den Abschalttimer wieder auf"""
        self.Timer = Ansteuerzeit_Sek * 100  # Skalierung auf 10ms Raster
        self._BeeperON()
        log.debug(f"Starte Beeper mit {Ansteuerzeit_Sek} Sek")

    def _BeeperOFF(self):
        log.debug(f"Beeper OFF")
        if not self.demo_modus:
            GPIO.output(self.BeeperpinNr, True)

    def _BeeperON(self):
        log.debug(f"Beeper ON")
        if not self.demo_modus:
            GPIO.output(self.BeeperpinNr, False)
