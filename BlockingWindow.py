import platform
import tkinter as tk
from tkinter import PhotoImage

class BlockingWindow(tk.Toplevel):

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
        if self.master.demo_modus:
            self.title(title)
            self.geometry(self.master.geometry())
        else:
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
