import platform
import tkinter as tk

class FakeBlackscreen(tk.Toplevel):
    """
    Legt ein Vollbildfenster auf den Screen der erst durch einmaliges beruehren des Bildschirms deaktiviert wird.
    Soll verhindern das wenn man auf einen abgeschalteten Bildschirm tippt ein Event ausloest.
    """

    def __init__(self, master, seconds: int, bg_color: str = "#000000") -> None:
        super().__init__(master=master)
        self.master = master

        if master.demo_modus:
            self.title("FakeBackscreen")
        else:
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

        self.withdraw() # Hide Window
        self.Timer = self.milliseconds
        self.timer_countdown()


    def mausklick(self, event=None):
        '''Zieht den Timer fuer den Blackscreen neu auf'''
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
                self.geometry(self.master.geometry())
                self.deiconify() # Show again
                self.attributes("-topmost", 1)
                self.attributes("-topmost", 0)
        
        self.master.after(100, self.timer_countdown)
