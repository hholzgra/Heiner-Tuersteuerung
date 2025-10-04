from pathlib import Path
import tkinter as tk
import binascii
import signal
import sys
import time
import os
from dataclasses import dataclass
from threading import Timer, Thread
import requests
import argparse
from gui import GUI, GuiEventConsumer, GuiEventProducer, GUI_EVENTS
from RelaisSteuerung import RelaisSteuerung
from BeeperSteuerung import BeeperSteuerung
import threading
import platform

import logging
import traceback

from Settings import Settings

# Logging initialisieren
log = logging.getLogger("Tuersteuerung")
log.setLevel(logging.INFO)

# Logging ins SystemD Journal wenn wir als Service laufen
if 'INVOCATION_ID' in os.environ:
    from systemd.journal import JournalHandler
    log.addHandler(JournalHandler())
    
sys.excepthook = exceptionLogging
    
class EventConsumer(GuiEventConsumer):

    def __init__(
        self,
        relais_str: RelaisSteuerung,
        beeper_strg: BeeperSteuerung,
        einstellungen_file: Path = Path("einstellungen.txt"),
    ) -> None:
        super().__init__()
        self.relais_str = relais_str
        self.beeper_strg = beeper_strg

        settings = Settings()

        telegram = settings.get("telegram")
        self.Setup_TOKEN: str = telegram["TOKEN"]
        self.Setup_CHAT_ID: str = telegram["CHAT_ID"]

        namen = settings.get("namen")
        self.Setup_list_namen: list = [
            namen["oben"],
            namen["mitte"],
            namen["unten"],
        ]

    def notify(self, event: GUI_EVENTS):
        """Wird vom GUI aufgerufen wenn ein Click/Oeffner Event statt fand"""
        print("----")
        if event == GUI_EVENTS.KLINGEL_1:
            self.relais_str.TriggerRelais(
                RelaisSteuerung.RELAIS_2, Ansteuerzeit_Sek=1
            )  # Klingel oben
            self.telegram.bot_notification(
                "Klingel `" + self.Setup_list_namen[0] + "`."
            )
            self.beeper_strg.TriggerBeeper(Ansteuerzeit_Sek=0.5)

        elif event == GUI_EVENTS.KLINGEL_2:
            self.relais_str.TriggerRelais(
                RelaisSteuerung.RELAIS_3, Ansteuerzeit_Sek=1
            )  # Klingel mitte
            self.telegram_bot_notification(
                "Klingel `" + self.Setup_list_namen[1] + "`."
            )
            self.beeper_strg.TriggerBeeper(Ansteuerzeit_Sek=0.5)

        elif event == GUI_EVENTS.BRIEFKASTEN:
            self.relais_str.TriggerRelais(
                RelaisSteuerung.RELAIS_4, Ansteuerzeit_Sek=1
            )  # Briefkasten unten
            self.telegram_bot_notification("Briefkasten wurde geöffnet.")
            self.beeper_strg.TriggerBeeper(Ansteuerzeit_Sek=0.5)

        elif event == GUI_EVENTS.TUER_OEFFNER:
            self.relais_str.TriggerRelais(
                RelaisSteuerung.RELAIS_1, Ansteuerzeit_Sek=2
            )  # Tueroeffner Relais
            self.telegram_bot_notification("Tür wurde mit Code geöffnet.")

        elif event == GUI_EVENTS.SHUTDOWN_EVT:
            # hier koennte ihr shutdown-befehl stehen
            pass

        if args.demomodus:
            print(f"Consumer got Message: {event}")


    def telegram_bot_notification(self, message: str):
        """Sendet eine Nachricht an den mit TOKEN und CHAT_ID konfigurierten Telegram Bot"""

        url = f"https://api.telegram.org/bot{self.Setup_TOKEN}/sendMessage?chat_id={self.Setup_CHAT_ID}&text={message}"

        if args.demomodus:
            print(f"DEMO::TelegramMsg:  {url}")
            return

        try:
            requests.get(url)
            print("GESENDET")
        except:
            print("SENDE FEHLER")
            pass


# Called on process interruption. Set all pins to "Input" default mode.
def endProcess(signalnum=None, handler=None):
    stop_event.set()
    relais_str.ALLOFF()
    sys.exit()

def exceptionLogging(*exc_info):
    text = "".join(traceback.format_exception(*exc_info()))
    log.error("#### Tuersystem GUI Exception ####")
    log.error("Unhandled exception: %s", text)


################################################################################
################################################################################
#################################   START   ####################################
################################################################################
################################################################################

if __name__ == '__main__':
    # Kommandozeilen-Parser initialisieren
    parser = argparse.ArgumentParser(description="")
    
    # Kommandozeilen-Optionen hinzufügen
    parser.add_argument(
        "--demomodus",
        action="store_true",
        help="Deaktiviert Dinge die auf einem nicht-PI nicht funktionieren und erzeugt zusaetzliche Consolen Ausgaben",
    )

    # Kommandozeile auswerten
    global args
    args, unknown = parser.parse_known_args()


    signal.signal(signal.SIGINT,  endProcess)
    signal.signal(signal.SIGTERM, endProcess)

    stop_event = threading.Event()
    
    relais_str = RelaisSteuerung(stop_event=stop_event, demo_modus=args.demomodus)
    relais_str.start()

    beeper_strg = BeeperSteuerung(stop_event=stop_event, demo_modus=args.demomodus)
    beeper_strg.start()

    localpath = os.path.dirname(__file__)
    file_path = Path(Path(localpath) / "einstellungen.txt")

    eventConsumer = EventConsumer(
        relais_str=relais_str, beeper_strg=beeper_strg, einstellungen_file=file_path
    )

    gui = GUI(
        einstellungen_file=file_path, beeper_strg=beeper_strg, demo_modus=args.demomodus
    )
    
    gui.register(eventConsumer)
    gui.bind("<Escape>", lambda event: gui.quit())
    gui.protocol("WM_DELETE_WINDOW", endProcess)
    gui.mainloop()


    stop_event.set()
