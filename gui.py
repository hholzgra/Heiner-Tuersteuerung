import os
import math
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

from Settings import Settings

# from PIL import ImageTk, Image
from tkinter import PhotoImage
from BeeperSteuerung import BeeperSteuerung
import threading

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
                BlockingWindows(
                    self,
                    seconds=3,
                    title=f"Klingel",
                    subtitle=self.Setup_list_namen[0],
                    bild=self.Setup_GlockenBild,
                )

            elif gui_event == GUI_EVENTS.KLINGEL_2:
                # BildPopup(self, seconds=3, x_pos=event.x, y_pos=y_berechnet, bild=self.Setup_GlockenBild) # event.y ist relativ zum jeweiligen "klingelschild" 3x 160px vertikal
                BlockingWindows(
                    self,
                    seconds=3,
                    title=f"Klingel",
                    subtitle=self.Setup_list_namen[1],
                    bild=self.Setup_GlockenBild,
                )

            elif gui_event == GUI_EVENTS.BRIEFKASTEN:
                # BildPopup(self, seconds=3, x_pos=event.x, y_pos=y_berechnet, bild=self.Setup_BriefBild) # event.y ist relativ zum jeweiligen "klingelschild" 3x 160px vertikal
                BlockingWindows(
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
                # highlightbackground="#111111",
                # highlightcolor="#111111",
                font=self.my_font,
                compound="center",
                # justify="center",
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

        # label = tk.Label(frame, text="", background="#424242")
        # label.grid(column=0, columnspan=self.columns, pady=20, padx=0)

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
        # print(f"sliding_window_tuer_code: {self.sliding_window_tuer_code}")
        # print(f"len(self.secret_tuer_code): {len(self.secret_tuer_code)}")
        # print(f"self.secret_tuer_code: {self.secret_tuer_code}")
        if len(self.sliding_window_tuer_code) > len(self.secret_tuer_code):
            self.sliding_window_tuer_code.reverse()
            self.sliding_window_tuer_code.pop()
            self.sliding_window_tuer_code.reverse()

        # print("Es wurde " + str(value) + " geklickt")
        # print(self.sliding_window_tuer_code)

        if self.sliding_window_tuer_code == self.secret_tuer_code:
            BlockingWindows(self.master, seconds=3, title="Tuer ist offen")
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

            # print("Es wurde " + str(value) + " geklickt")
            # print(self.sliding_window_shutdown)

            if self.sliding_window_shutdown == self.secret_shutdown_code:
                BlockingWindows(
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
                BlockingWindows(
                    self, seconds=self.secret_timeout, title="Wird verarbeitet ..."
                )
            )
            self.destroy()


class BlockingWindows(tk.Toplevel):

    def __init__(
        self,
        master,
        seconds: int = 5,
        title: str = "Wartebildschirm",
        subtitle: str = "",
        bild: tk.PhotoImage = None,
        bg_color: str = "#222222",
        fg_color: str = "#EEEEEE",
    ) -> None:
        super().__init__(master=master)
        self.master = master

        # Titelzeile entfernen
        self.overrideredirect(True)
        self.geometry("800x480")
        self.config(cursor="none", background=bg_color)
        self.seconds = seconds

        self.title = title

        frame = tk.Frame(self, width=800, height=480, background=bg_color)
        frame.place(relwidth=1.0, relheight=1.0, relx=0.5, rely=0.5, anchor="center")

        # Einzeiliger Text (Bild Optional)
        if subtitle == "":
            label = tk.Label(
                frame,
                text=self.title,
                background=bg_color,
                foreground=fg_color,
                font=("Helvetica 50 bold"),
            )
            label.place(
                relwidth=1.0, relheight=1.0, relx=0.5, rely=0.5, anchor="center"
            )

            if bild != None:
                label_bild = tk.Label(
                    frame,
                    image=bild,
                    background=bg_color,
                )
                label_bild.place(
                    width=bild.width(), height=bild.height(), x=400, y=0, anchor="n"
                )

        # Mehrzeiliger Text (Bild Optional)
        else:
            label = tk.Label(
                frame,
                text=self.title,
                background=bg_color,
                foreground=fg_color,
                font=("Helvetica 50 bold"),
            )
            label.pack(fill="x", pady=50)
            label2 = tk.Label(
                frame,
                text=subtitle.replace("  ", ""),
                background=bg_color,
                foreground=fg_color,
                font=("Helvetica 40 bold"),
            )
            label2.pack(fill="x", pady=70)

            if bild != None:
                label_bild = tk.Label(
                    frame,
                    image=bild,
                    background=bg_color,
                )
                label_bild.place(width=bild.width(), height=bild.height(), x=30, y=0)

        self.master.after(seconds * 1000, self.destroy)


class BildPopup(tk.Toplevel):

    def __init__(
        self, master, bild: PhotoImage, x_pos, y_pos, seconds=3, x_anim_offset_px=10
    ) -> None:
        super().__init__(master=master)
        self.master = master

        self.sidelength = bild.height() + x_anim_offset_px

        # Titelzeile entfernen
        self.overrideredirect(True)
        geometry = f"{self.sidelength}x{self.sidelength}+{int(x_pos-self.sidelength/2)}+{int(y_pos-self.sidelength/2)}"
        self.geometry(geometry)

        if platform.uname().system == "Linux" and platform.uname().node == "raspberrypi":
            background_color = "#424242"  # Unter Windows Transparenz Farbe
            self.attributes("-transparentcolor", background_color)
        else:
            # self.wm_attributes("-transparent", True) # Geht nicht
            # self.config(cursor="none", bg="systemTransparent") # Geht nicht
            background_color = "#111111"
            pass

        self.config(
            cursor="none",
            background=background_color,
        )

        self.seconds = seconds

        # self.attributes('-alpha', 0.2)

        self.frame = tk.Frame(
            self,
            width=self.sidelength,
            height=self.sidelength,
            background=background_color,
        )
        self.frame.pack(fill="both", expand=True)

        self.label = tk.Label(
            self.frame,
            text=" ",
            image=bild,
            background=background_color,
            foreground="#EEEEEE",
            font=("Helvetica 50 bold"),
        )
        self.label.place(anchor="nw", x=0, y=0, relheight=1.0, relwidth=1.0)

        # self.animation_gross = True
        # self.animation_temp_sidelength = self.sidelength
        self.y_pos = y_pos
        self.x_pos = x_pos
        self.animation_y_pos = y_pos
        self.anim_pos_toggle = True
        self.x_offset = 0
        self.animation_alpha = 1.0
        self.x_anim_offset_px = x_anim_offset_px
        self.anim_start = time.time_ns()

        self.anim_Lock = threading.Lock()
        self.destroy_Lock = threading.Lock()

        self.animate()
        self.master.after(seconds * 1000, self.destroy)

    def destroy(self) -> None:
        """Die Locks sollen verhindern das die sich selbst aufrufende self.animation() auf ein ungueltiges Objekt zugreift"""
        if not self.destroy_Lock.locked():
            self.destroy_Lock.acquire()  # verhindere weitere Animationsschleifen

        if self.anim_Lock.locked():  # Wait for animation to be done
            self.master.after(200, self.destroy)

        return super().destroy()

    def animate(self, anim_recall_ms: int = 10, anim_range_px: int = 100):
        """Animiert das angezeigte Bild, Lock()'s beachten"""
        if not self.destroy_Lock.locked():

            if not self.anim_Lock.locked():
                self.anim_Lock.acquire()

            # # Animation: Groesse
            # if self.animation_gross: # groesser werden
            #     self.animation_temp_sidelength += anim_range_px
            #     if self.animation_temp_sidelength > self.sidelength + anim_range_px:
            #         self.animation_gross = False
            # else: # kleiner werden
            #     self.animation_temp_sidelength -= anim_range_px
            #     if self.animation_temp_sidelength < self.sidelength - anim_range_px:
            #         self.animation_gross = True
            # self.configure(width=self.animation_temp_sidelength, height=self.animation_temp_sidelength)

            # Animation: Position
            # Exponential Smoothing: position += (target - position) * (1 - exp(- speed * dt))
            # siehe: https://lisyarus.github.io/blog/posts/exponential-smoothing.html

            target_offset_plus = int(self.x_anim_offset_px / 2)
            target_offset_minus = -int(self.x_anim_offset_px / 2)
            speed_dt = 0.2

            if self.anim_pos_toggle:
                # self.x_offset += 1
                self.x_offset += (target_offset_plus - self.x_offset) * (
                    1 - math.exp(-speed_dt)
                )
                if self.x_offset > target_offset_plus - 1:
                    self.anim_pos_toggle = False
            else:
                # self.x_offset -= 1
                self.x_offset += (target_offset_minus - self.x_offset) * (
                    1 - math.exp(-speed_dt)
                )
                if self.x_offset < target_offset_minus + 1:
                    self.anim_pos_toggle = True

            self.label.place(
                anchor="nw", x=self.x_offset, y=0, relheight=1.0, relwidth=1.0
            )

            # Animation: Alpha
            alpha_reduction_factor = anim_recall_ms / (
                self.seconds * 1000
            )  # Fuer lineares Alpha in z.B. 3 Sekunden von 1.0 auf 0.0 bei 10 ms Aufrufen

            self.animation_alpha = max(
                0.0,
                self.animation_alpha
                - alpha_reduction_factor
                + (time.time_ns() - self.anim_start) / self.anim_start,
            )
            self.attributes("-alpha", self.animation_alpha)
            self.master.after(10, self.animate)
        else:
            self.anim_Lock.release()


class FakeBlackscreen(tk.Toplevel):
    """
    Legt ein Vollbildfenster auf den Screen der erst durch einmaliges beruehren des Bildschirms deaktiviert wird.
    Soll verhindern das wenn man auf einen abgeschalteten Bildschirm tippt ein Event ausloest.
    """

    def __init__(self, master, seconds: int, bg_color: str = "#000000") -> None:
        super().__init__(master=master)
        self.master = master

        # Titelzeile entfernen
        self.overrideredirect(True)
        self.geometry("800x480")
        self.config(cursor="none", background=bg_color)
        self.milliseconds = seconds * 1000
        self.bind("<Button-1>", self.mausklick)

        frame = tk.Frame(self, width=800, height=480, background=bg_color)
        label = tk.Label(frame, background=bg_color)
        label.pack(expand=True, fill="both")
        frame.place(relwidth=1.0, relheight=1.0, relx=0.5, rely=0.5, anchor="center")

        self.lift(aboveThis=master)
        self.attributes("-topmost", 1)
        self.attributes("-topmost", 0)

        if platform.uname().system == "Linux" and platform.uname().node == "raspberrypi":
            self.input_prev_state = GPIO.input(pinNr)

        self.Timer = 0
        self.timer_countdown()


    def mausklick(self, event=None):
        '''Zieht den Timer fuer den Blackscreen neu auf'''
        # self.master.lift(aboveThis=self)
        self.withdraw() # Hide Window
        self.Timer = self.milliseconds

    def timer_countdown(self):

        if platform.uname().system == "Linux" and platform.uname().node == "raspberrypi":
            # Retriggern wenn der Sensor Bewegung meldet (Flankenauswertung)
            input_value = GPIO.input(pinNr)
            if input_value == False and self.input_prev_state == True:
                self.withdraw() # Hide Window
                self.Timer = self.milliseconds
            self.input_prev_state = input_value

        if self.Timer != 0:
            self.Timer -= 100 # Aufruf Raster beachten
            self.Timer = max(0, self.Timer)

            if self.Timer <= 0:
                self.deiconify() # Show again
                self.attributes("-topmost", 1)
                self.attributes("-topmost", 0)
        
        self.master.after(100, self.timer_countdown)


