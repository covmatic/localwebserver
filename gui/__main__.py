import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
from .robot_buttons import RobotButtonFrame
from .app_buttons import AppButtonFrame
from . import _icon_url, _icon_file, _ot_2_ip
import requests
import os


def set_ico(parent, url: str = _icon_url, file: str = _icon_file):
    if not os.path.exists(file):
        response = requests.get(url)
        with open(file, 'wb') as f:
            f.write(response.content)
    if os.path.exists(file) and os.path.isfile(file):
        icon = ImageTk.PhotoImage(Image.open(file))
        parent.tk.call('wm', 'iconphoto', root._w, icon)
    

class Covmatic(tk.Frame):
    def __init__(self,
        parent: tk.Tk,
        *args, **kwargs
    ):
        super(Covmatic, self).__init__(parent, *args, **kwargs)
        self._ip_label = tk.Label(text=_ot_2_ip)
        self._robot_buttons = RobotButtonFrame(self)
        self._app_buttons = AppButtonFrame(self)
        
        self._ip_label.grid(row=0)
        self._robot_buttons.grid(row=1, column=0, sticky=tk.N)
        self._app_buttons.grid(row=1, column=1, sticky=tk.N)


if __name__ == "__main__":
    root = tk.Tk()
    root.title('Covmatic GUI')
    set_ico(root)
    
    if _ot_2_ip:
        covmatic = Covmatic(root)
        covmatic.grid()
    else:
        root.withdraw()
        tk.messagebox.showwarning("Robot IP", "Robot IP address not set.\nPlease set the environment variable:\n\nOT2IP")
        root.destroy()
    
    root.mainloop()
