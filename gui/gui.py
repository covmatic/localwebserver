import tkinter as tk
from .args import Args
from .robot_buttons import RobotButtonFrame
from .app_buttons import AppButtonFrame
from .images import get_logo
from .barcodeserver import BarcodeServerThread


class Covmatic(tk.Frame):
    def __init__(self,
        parent: tk.Tk,
        *args, **kwargs
    ):
        super(Covmatic, self).__init__(parent, *args, **kwargs)
        self._ip_label = tk.Label(self, text=Args().ip)
        self._empty_label = tk.Label(self, text=" ")
        self._logo_photo = get_logo(resize=0.1)
        self._logo = tk.Label(self, image=self._logo_photo)
        self._robot_buttons = RobotButtonFrame(self)
        self._app_buttons = AppButtonFrame(self)
        
        self._logo.grid(row=0, columnspan=2)
        self._ip_label.grid(row=1, columnspan=2)
        self._empty_label.grid(row=2, columnspan=2)
        self._robot_buttons.grid(row=3, column=0, sticky=tk.N)
        self._app_buttons.grid(row=3, column=1, sticky=tk.N)
        self._barcode_server = BarcodeServerThread(self)
        self._barcode_server.start()
    
    def destroy(self):
        super(Covmatic, self).destroy()
