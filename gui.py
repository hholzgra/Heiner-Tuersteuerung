import os
import platform
import pprint
import tkinter as tk
import tkinter.ttk as ttk
import time
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
import sys
import logging
from Settings import Settings

# from PIL import ImageTk, Image
from tkinter import PhotoImage

from BeeperSteuerung import BeeperSteuerung
from FakeBlackscreen import FakeBlackscreen
from BlockingWindow  import BlockingWindow
from KeyPad          import KeyPad

# Logging initialisieren
log = logging.getLogger("Tuersteuerung")

if platform.uname().system == "Linux" and platform.uname().node == "raspberrypi":
    import RPi.GPIO as GPIO
    pinNr = 19
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pinNr, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Achtung dies Setup wird auch vom BacklighControll Service gemacht!!!

class GUI_EVENTS(Enum):
    KLINGEL_1 = 0
    KLINGEL_2 = 1
    BRIEFKASTEN = 2
    TUER_OEFFNER = 3
    SHUTDOWN_EVT = 4


class GuiEventConsumer(ABC):

    @abstractmethod
    def notify(self, event: GUI_EVENTS):
        pass


class GuiEventProducer(ABC):

    @abstractmethod
    def register(self, consumer: GuiEventConsumer):
        pass

    @abstractmethod
    def unregister(self, consumer: GuiEventConsumer):
        pass


class GUI(tk.Tk, GuiEventProducer):

    def __init__(
        self,
        beeper_strg: BeeperSteuerung,
        demo_modus=False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__()

        self.beeper_strg = beeper_strg

        self.title("Tuersteuerung")
        self.geometry("800x480+0+0")
        self.configure(background="#424242")

        self.demo_modus = demo_modus

        if not demo_modus:
            self.config(cursor="none", background="black", bg="black", borderwidth=0)
            self.attributes("-fullscreen", True)

        self.text_spacer: str = "         "
        self.my_font: tuple = "Helvetica 22 bold"

        self.ConsumerList: list[GuiEventConsumer] = []
        self.buttons: list[ttk.Button] = []

        self.keypad = None

        settings = Settings()

        namen = settings.get("namen")
        self.Setup_list_namen: list = [
            namen["oben"],
            namen["mitte"],
            namen["unten"],
        ]

        secrets = settings.get("tuer")
        self.Setup_secret_tuer_code: list     = secrets["zugangs_code"]
        self.Setup_secret_shutdown_code: list = secrets["herunterfahren"]

        localpath = Path(os.path.dirname(__file__))
        imagepath = localpath / Path("bilder")
        self.Setup_BG_Bilder = [
            PhotoImage(file=imagepath / Path("img_1.png")),
            PhotoImage(file=imagepath / Path("img_2.png")),
            PhotoImage(file=imagepath / Path("img_3.png")),
        ]

        self.Setup_GlockenBild = PhotoImage(file=imagepath / Path("glocke_mittel.png"))
        self.Setup_BriefBild = PhotoImage(file=imagepath / Path("brief_mittel.png"))

        self.build()

        self.black_screen = FakeBlackscreen(self, seconds=20)

    def register(self, consumer: GuiEventConsumer):
        self.ConsumerList.append(consumer)

    def unregister(self, consumer: GuiEventConsumer):
        self.ConsumerList.remove(consumer)

    def event_button_click(self, event: tk.Event, eventbutton: int):
        gui_event: GUI_EVENTS = None
        self.black_screen.mausklick()
        # Screen 800x640 .. Button-Tile 800x160
        # Unterer rechter 100x100 Bereich fuer Sonderfunktion auswerten
        # ggf. Keypad öffnen
        if eventbutton == 2 and event.x > 700 and event.y > 60:
            self.show_keypad()
        else:
            gui_event = GUI_EVENTS(eventbutton)
            self.publish_event(gui_event)

            # todo KlingelAnimation an x,y Position einblenden
            temp_y = min(
                110, max(90, event.y)
            )  # Position vertikal in das angewaehlte Feld ruecken
            y_berechnet = temp_y + eventbutton * 160  # genaue Position bestimmen

            if gui_event == GUI_EVENTS.KLINGEL_1:
                # BildPopup(self, seconds=3, x_pos=event.x, y_pos=y_berechnet, bild=self.Setup_GlockenBild) # event.y ist relativ zum jeweiligen "klingelschild" 3x 160px vertikal
                BlockingWindow(
                    self,
                    seconds=3,
                    title=f"Klingel",
                    subtitle=self.Setup_list_namen[0],
                    bild=self.Setup_GlockenBild,
                )

            elif gui_event == GUI_EVENTS.KLINGEL_2:
                # BildPopup(self, seconds=3, x_pos=event.x, y_pos=y_berechnet, bild=self.Setup_GlockenBild) # event.y ist relativ zum jeweiligen "klingelschild" 3x 160px vertikal
                BlockingWindow(
                    self,
                    seconds=3,
                    title=f"Klingel",
                    subtitle=self.Setup_list_namen[1],
                    bild=self.Setup_GlockenBild,
                )

            elif gui_event == GUI_EVENTS.BRIEFKASTEN:
                # BildPopup(self, seconds=3, x_pos=event.x, y_pos=y_berechnet, bild=self.Setup_BriefBild) # event.y ist relativ zum jeweiligen "klingelschild" 3x 160px vertikal
                BlockingWindow(
                    self,
                    seconds=3,
                    title=f"Öffne Briefkasten",
                    bild=self.Setup_BriefBild,
                )

    def publish_event(self, gui_event: GUI_EVENTS):

        for consumer in self.ConsumerList:
            consumer.notify(gui_event)

    def build(self):

        frame = ttk.Frame(self, width=800, height=480, border=0, borderwidth=0)

        # Generate main buttons
        for i in range(0, 3):

            btn = ttk.Label(
                frame,
                border=22,
                borderwidth=0,
                image=self.Setup_BG_Bilder[i],
                foreground="#111111",
                background="#111111",
                text=self.text_spacer + self.Setup_list_namen[i],
                font=self.my_font,
                compound="center",
            )

            cmd_for_btn = lambda event, idx=i: self.event_button_click(event, idx)

            btn.bind("<Button-1>", cmd_for_btn)
            btn.place(
                x=0,
                y=i * 160,
                width=800,
                height=160,
            )
            self.buttons.append(btn)

        frame.pack(expand=True, fill="both")

    def show_keypad(self):
        reply = ""
        if self.keypad != None:
            self.keypad.destroy()

        self.keypad = KeyPad(
            self,
            beeper_strg=self.beeper_strg,
            callback_any_btn_clicked=self.black_screen.mausklick,
            callback_oeffner=lambda evt=GUI_EVENTS.TUER_OEFFNER: self.publish_event(
                evt
            ),
            callback_shutdown=lambda evt=GUI_EVENTS.SHUTDOWN_EVT: self.publish_event(
                evt
            ),
            secret_tuer_code=self.Setup_secret_tuer_code,
            secret_shutdown_code=self.Setup_secret_shutdown_code,
            demo_modus=self.demo_modus,
        )
        self.wait_window(window=self.keypad)


# Inspiration: https://github.com/RogerWoollett/Keypad/blob/main/Trypad.py


