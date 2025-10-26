import tkinter as tk
import logging
import random

from BeeperSteuerung import BeeperSteuerung
from BlockingWindow  import BlockingWindow

# Logging initialisieren
log = logging.getLogger("Tuersteuerung")

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


