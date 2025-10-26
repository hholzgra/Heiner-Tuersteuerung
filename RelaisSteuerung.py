import threading
import time
import logging

# Logging initialisieren
log = logging.getLogger("Tuersteuerung")

class RelaisSteuerung(threading.Thread):

    RELAIS_COUNT = 4
    RELAIS_1 = 0
    RELAIS_2 = 1
    RELAIS_3 = 2
    RELAIS_4 = 3

    DEFAULT_ANSTEUERZEIT_SEK = 1
    ALL_OFF = 0xFF

    def __init__(self, stop_event: threading.Event, demo_modus=False) -> None:
        super().__init__()

        self.demo_modus = demo_modus
        self.stop_event = stop_event

        self.DEVICE_ADDRESS = (
            0x20  # 7 bit address (will be left shifted to add the read write bit)
        )
        self.DEVICE_REG_MODE1 = 0x06
        self.DEVICE_REG_DATA = self.ALL_OFF
        if not self.demo_modus:
            import smbus

            self.bus = smbus.SMBus(
                1
            )  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
            self.bus.write_byte_data(
                self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA
            )

        # Laufzeit Timer fuer jedes der 4 Relais
        self.Timer        = []
        self.func_list_ON : list[callable]  = []
        self.func_list_OFF: list[callable]  = []

        for id in range(0, self.RELAIS_COUNT):
            self.Timer.append(0)
            self.func_list_ON.append( lambda id=id: self.SWITCH(id, True))
            self.func_list_OFF.append(lambda id=id: self.SWITCH(id, False))

    def run(self):
        while not self.stop_event.is_set():
            time.sleep(0.1)
            for i, _ in enumerate(self.Timer):
                if self.Timer[i] > 0:
                    self.Timer[i] = (
                        self.Timer[i] - 1
                    )  # der Timerwert entspricht 100ms Raster
                    if self.Timer[i] == 0:
                        # Timer hat Null erreicht, Relais abschalten
                        self.func_list_OFF[i]()
                        log.debug(bin(self.DEVICE_REG_DATA))

    def TriggerRelais(
        self, relais_nummer: int, Ansteuerzeit_Sek: int = DEFAULT_ANSTEUERZEIT_SEK
    ) -> None:
        """Schaltet ein Relais ein und zieht den Abschalttimer wieder auf"""
        log.debug(f"Starte Nr {relais_nummer} mit {Ansteuerzeit_Sek} Sek")
        self.Timer[relais_nummer] = Ansteuerzeit_Sek * 10  # Skalierung auf 100ms Raster
        self.func_list_ON[relais_nummer]()
        log.debug(bin(self.DEVICE_REG_DATA))

    def ALLOFF(self):
        for func_off in self.func_list_OFF:
            func_off()

    def SWITCH(self, relais_nr, state_on) -> None:
        log.debug("Relais #%d switch %s" % (relais_nr + 1, "ON" if state_on else "OFF"))
        if state_on:
            self.DEVICE_REG_DATA &= ~(0x1 << relais_nr)
        else: # off
            self.DEVICE_REG_DATA |= 0x1 << relais_nr
        if not self.demo_modus:
            self.bus.write_byte_data(
                self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA
            )
