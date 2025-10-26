import math
import platform
import threading
import time
import tkinter as tk
from tkinter import PhotoImage

class BildPopup(tk.Toplevel):

    def __init__(
        self, master, bild: PhotoImage, x_pos, y_pos, seconds=3, x_anim_offset_px=10
    ) -> None:
        super().__init__(master=master)
        self.master = master
        self.sidelength = bild.height() + x_anim_offset_px

        if self.master.demo_modus:
            self.title("BildPopup")
        else:
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
                self.x_offset += (target_offset_plus - self.x_offset) * (
                    1 - math.exp(-speed_dt)
                )
                if self.x_offset > target_offset_plus - 1:
                    self.anim_pos_toggle = False
            else:
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
