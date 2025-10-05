import tkinter as tk
import signal
import sys
import os
from dataclasses import dataclass
from threading import Timer, Thread
import requests
import argparse
from gui import GUI, GuiEventConsumer, GuiEventProducer, GUI_EVENTS
import threading

import logging
import traceback

from Settings import Settings
from RelaisSteuerung import RelaisSteuerung
from BeeperSteuerung import BeeperSteuerung
import Telegram

# Logging initialisieren
log = logging.getLogger("Tuersteuerung")
log.setLevel(logging.INFO)

# Logging ins SystemD Journal wenn wir als Service laufen
if os.getppid() == 1:
    from systemd.journal import JournalHandler
    log.addHandler(JournalHandler())
    
def exceptionLogging(*exc_info):
    text = "".join(traceback.format_exception(*exc_info))
    log.error("#### Tuersystem GUI Exception ####")
    log.error("Unhandled exception: %s", text)

sys.excepthook = exceptionLogging
    
class EventConsumer(GuiEventConsumer):

    def __init__(
        self,
        relais_strg: RelaisSteuerung,
        beeper_strg: BeeperSteuerung,
    ) -> None:
        super().__init__()
        self.relais_strg = relais_strg
        self.beeper_strg = beeper_strg

        settings = Settings()

        namen = settings.get("namen")
        self.Setup_list_namen: list = [
            namen["oben"],
            namen["mitte"],
            namen["unten"],
        ]

    def notify(self, event: GUI_EVENTS):
        """Wird vom GUI aufgerufen wenn ein Click/Oeffner Event statt fand"""
        log.debug("----")
        if event == GUI_EVENTS.KLINGEL_1:
            self.relais_strg.TriggerRelais(
                RelaisSteuerung.RELAIS_2, Ansteuerzeit_Sek=1
            )  # Klingel oben
            Telegram.bot_notification(
                "Klingel `" + self.Setup_list_namen[0] + "`.",
                args.demomodus
            )
            self.beeper_strg.TriggerBeeper(Ansteuerzeit_Sek=0.5)

        elif event == GUI_EVENTS.KLINGEL_2:
            self.relais_strg.TriggerRelais(
                RelaisSteuerung.RELAIS_3, Ansteuerzeit_Sek=1
            )  # Klingel mitte
            Telegram.bot_notification(
                "Klingel `" + self.Setup_list_namen[1] + "`.",
                args.demomodus
            )
            self.beeper_strg.TriggerBeeper(Ansteuerzeit_Sek=0.5)

        elif event == GUI_EVENTS.BRIEFKASTEN:
            self.relais_strg.TriggerRelais(
                RelaisSteuerung.RELAIS_4, Ansteuerzeit_Sek=1
            )  # Briefkasten unten
            Telegram.bot_notification(
                "Briefkasten wurde geöffnet.",
                args.demomodus
            )
            self.beeper_strg.TriggerBeeper(Ansteuerzeit_Sek=0.5)

        elif event == GUI_EVENTS.TUER_OEFFNER:
            self.relais_strg.TriggerRelais(
                RelaisSteuerung.RELAIS_1, Ansteuerzeit_Sek=2
            )  # Tueroeffner Relais
            Telegram.bot_notification(
                "Tür wurde mit Code geöffnet.",
                args.demomodus
            )

        elif event == GUI_EVENTS.SHUTDOWN_EVT:
            # hier koennte ihr shutdown-befehl stehen
            pass

        log.debug(f"Consumer got Message: {event}")


# Called on process interruption. Set all pins to "Input" default mode.
def endProcess(signalnum=None, handler=None):
    stop_event.set()
    relais_strg.ALLOFF()
    sys.exit()



################################################################################
################################################################################
#################################   START   ####################################
################################################################################
################################################################################

if __name__ == '__main__':
    # Kommandozeilen-Parser initialisieren
    parser = argparse.ArgumentParser(description="Tuersteuerung")
    
    # Kommandozeilen-Optionen hinzufügen
    parser.add_argument(
        "--demomodus",
        action="store_true",
        help="Deaktiviert Dinge die auf einem nicht-PI nicht funktionieren und erzeugt zusaetzliche Consolen Ausgaben",
    )

    # Kommandozeile auswerten
    global args
    args = parser.parse_args()

    if args.demomodus:
        log.setLevel(logging.DEBUG)

    signal.signal(signal.SIGINT,  endProcess)
    signal.signal(signal.SIGTERM, endProcess)

    stop_event = threading.Event()
    
    relais_strg = RelaisSteuerung(stop_event=stop_event, demo_modus=args.demomodus)
    relais_strg.start()

    beeper_strg = BeeperSteuerung(stop_event=stop_event, demo_modus=args.demomodus)
    beeper_strg.start()

    localpath = os.path.dirname(__file__)

    eventConsumer = EventConsumer(
        relais_strg=relais_strg, beeper_strg=beeper_strg
    )

    gui = GUI(
        beeper_strg=beeper_strg, demo_modus=args.demomodus
    )
    
    gui.register(eventConsumer)
    gui.bind("<Escape>", lambda event: gui.quit())
    gui.protocol("WM_DELETE_WINDOW", endProcess)
    gui.mainloop()


    stop_event.set()
