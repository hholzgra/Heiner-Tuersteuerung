import threading
import time


class RelaisSteuerung(threading.Thread):

    RELAIS_1 = 0
    RELAIS_2 = 1
    RELAIS_3 = 2
    RELAIS_4 = 3
    DEFAULT_ANSTEUERZEIT_SEK = 1

    def __init__(self, stop_event:threading.Event, demo_modus=False) -> None:
        super().__init__()

        self.demo_modus = demo_modus
        self.stop_event = stop_event


        self.DEVICE_ADDRESS = 0x20  # 7 bit address (will be left shifted to add the read write bit)
        self.DEVICE_REG_MODE1 = 0x06
        self.DEVICE_REG_DATA = 0xff
        if not self.demo_modus:
            import smbus
            self.bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

        # Laufzeit Timer fuer jedes der 4 Relais
        self.Timer = [0, 0, 0, 0]
        self.func_list_ON:list[callable] = [self.ON_1, self.ON_2, self.ON_3, self.ON_4 ]
        self.func_list_OFF:list[callable] = [self.OFF_1, self.OFF_2, self.OFF_3, self.OFF_4 ]


    def run(self):
        
        while not self.stop_event.is_set():
            
            time.sleep(0.1)
            for i, _ in enumerate(self.Timer):
                if self.Timer[i] > 0:
                    self.Timer[i] = self.Timer[i]-1 # der Timerwert entspricht 100ms Raster
                    if self.Timer[i] == 0:
                        # Timer hat Null erreicht, Relais abschalten
                        self.func_list_OFF[i]()
                        if self.demo_modus:
                            print(bin(self.DEVICE_REG_DATA))




    def TriggerRelais(self, relais_nummer:int, Ansteuerzeit_Sek:int = DEFAULT_ANSTEUERZEIT_SEK) -> None:
        '''Schaltet ein Relais ein und zieht den Abschalttimer wieder auf'''
        self.Timer[relais_nummer] = Ansteuerzeit_Sek * 10  # Skalierung auf 100ms Raster
        self.func_list_ON[relais_nummer]()
        if self.demo_modus:
            print(f"Starte Nr {relais_nummer} mit {Ansteuerzeit_Sek} Sek")
            print(bin(self.DEVICE_REG_DATA))

    def fake_ON(self):
        pass

    def ALLOFF(self):
        for func_off in self.func_list_OFF:
            func_off()

    def ON_1(self) -> None:
        self.DEVICE_REG_DATA &= ~(0x1 << 0)
        if not self.demo_modus:
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def ON_2(self) -> None:
        self.DEVICE_REG_DATA &= ~(0x1 << 1)
        if not self.demo_modus:
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def ON_3(self) -> None:
        self.DEVICE_REG_DATA &= ~(0x1 << 2)
        if not self.demo_modus:
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def ON_4(self) -> None:
        self.DEVICE_REG_DATA &= ~(0x1 << 3)
        if not self.demo_modus:
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def OFF_1(self) -> None:
        self.DEVICE_REG_DATA |= (0x1 << 0)
        if not self.demo_modus:
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def OFF_2(self) -> None:
        self.DEVICE_REG_DATA |= (0x1 << 1)
        if not self.demo_modus:
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def OFF_3(self) -> None:
        self.DEVICE_REG_DATA |= (0x1 << 2)
        if not self.demo_modus:
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)

    def OFF_4(self) -> None:
        self.DEVICE_REG_DATA |= (0x1 << 3)
        if not self.demo_modus:
            self.bus.write_byte_data(self.DEVICE_ADDRESS, self.DEVICE_REG_MODE1, self.DEVICE_REG_DATA)
