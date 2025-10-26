import os
import platform
import pprint
import tkinter as tk
import tkinter.ttk as ttk
import random
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


class Key(tk.Label):
    # class for a key
    def __init__(self, master, callback, value=None, *args, **kwargs):
        tk.Label.__init__(
            self,
            master,
            takefocus=True,  # ,bd = 5
            relief=tk.RAISED,
            width=5,
            height=3,
            font=("Helvetica 20 bold"),
            *args,
            **kwargs,
        )

        self.value = value
        self.callback = callback

        self.bind("<Button-1>", self.on_over)
        self.bind("<ButtonRelease-1>", self.on_left)

    def on_left(self, x):
        self.configure(relief=tk.RAISED)
        # left mouse button released over key
        if self.cget("state") == tk.NORMAL:
            if self.value == None:
                self.callback()
            else:
                self.callback(self.value)

    def on_over(self, x):
        # left button pressed over key
        if self.cget("state") == tk.NORMAL:
            self.configure(relief=tk.SUNKEN)


class KeyPad(tk.Toplevel):

    number_buttons = []

    def __init__(
        self,
        master,
        beeper_strg: BeeperSteuerung,
        callback_any_btn_clicked: callable,
        keypad_rows: int = 4,
        keypad_columns: int = 6,
        callback_oeffner: callable = None,
        callback_shutdown: callable = None,
        secret_tuer_code: list[int] = [],
        secret_shutdown_code: list[int] = [],
        ddos_timeout: int = 30,
        ddos_max_input_length: int = 20,
        demo_modus=False,
    ) -> None:
        super().__init__(master=master, relief="ridge")

        self.master = master

        self.beeper_strg = beeper_strg

        self.callback_any_btn_clicked = callback_any_btn_clicked

        # Titelzeile entfernen
        self.overrideredirect(True)
        self.geometry("800x480")

        if not demo_modus:
            self.config(cursor="none", background="#424242")

        self.rows = keypad_rows
        self.columns = keypad_columns

        self.callback_tuer_relais = callback_oeffner
        self.callback_shutdown = callback_shutdown

        self.secret_tuer_code = secret_tuer_code

        self.secret_shutdown_code = secret_shutdown_code

        self.secret_timeout = ddos_timeout
        self.secret_max_input_length = ddos_max_input_length

        self.sliding_window_tuer_code = []
        self.sliding_window_shutdown = []
        self.try_counter = 0

        # Keypad schließt sich nach ein andertalb minuten selbst
        self.master.after(90000, self.destroy)

        frame = tk.Frame(self, width=800, height=480, background="#424242")
        frame.grid(row=self.rows, column=self.columns)

        btn_back = tk.Button(
            frame, text="Zurück", command=self.destroy, font=("Helvetica 20 bold")
        )
        btn_back.grid(column=0, columnspan=self.columns + 1, pady=20, padx=0)

        numbers = [*range(1, self.columns * self.rows + 1)]
        random.shuffle(numbers)

        for r in range(1, self.rows + 1):
            for c in range(1, self.columns + 1):
                num = numbers.pop()
                btn = Key(
                    frame,
                    text="  " + str(num) + "  ",
                    value=str(num),
                    callback=self.digit_clicked,
                ).grid(row=r, column=c)
                self.number_buttons.append(btn)

        frame.pack()

    def digit_clicked(self, value):
        
        self.callback_any_btn_clicked() # zieht den timer des `Fake Blackscreen` bei jedem Klick neu auf

        self.beeper_strg.TriggerBeeper(Ansteuerzeit_Sek=0.1)

        self.try_counter += 1

        # Tuerrelais Passwort abgleich
        self.sliding_window_tuer_code.append(int(value))
        log.debug(f"sliding_window_tuer_code: {self.sliding_window_tuer_code}")
        log.debug(f"len(self.secret_tuer_code): {len(self.secret_tuer_code)}")
        log.debug(f"self.secret_tuer_code: {self.secret_tuer_code}")
        if len(self.sliding_window_tuer_code) > len(self.secret_tuer_code):
            self.sliding_window_tuer_code.reverse()
            self.sliding_window_tuer_code.pop()
            self.sliding_window_tuer_code.reverse()

        log.debug("Es wurde " + str(value) + " geklickt")
        log.debug(self.sliding_window_tuer_code)

        if self.sliding_window_tuer_code == self.secret_tuer_code:
            BlockingWindow(self.master, seconds=3, title="Tuer ist offen")
            # self.master.after(5000, self.destroy)
            if self.callback_tuer_relais != None:
                self.callback_tuer_relais()  # "Keypad Tuer Event"
            # time.sleep(8)
            self.destroy()

        # Shutdown Passwort abgleich
        if len(self.secret_shutdown_code) > 0:
            self.sliding_window_shutdown.append(int(value))

            if len(self.sliding_window_shutdown) > len(self.secret_shutdown_code):
                self.sliding_window_shutdown.reverse()
                self.sliding_window_shutdown.pop()
                self.sliding_window_shutdown.reverse()

            log.debug("Es wurde " + str(value) + " geklickt")
            log.debug(self.sliding_window_shutdown)

            if self.sliding_window_shutdown == self.secret_shutdown_code:
                BlockingWindow(
                    self.master,
                    seconds=4,
                    title="An dieser Stelle kann\n der PI heruntergefahren\n werden",
                )
                # self.master.after(5000, self.destroy)
                if self.callback_shutdown != None:
                    self.callback_shutdown()  # "Keypad Shutdown Event"
                # time.sleep(8)
                self.destroy()

        if self.try_counter >= self.secret_max_input_length:
            self.wait_window(
                BlockingWindow(
                    self, seconds=self.secret_timeout, title="Wird verarbeitet ..."
                )
            )
            self.destroy()


