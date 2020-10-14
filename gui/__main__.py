import tkinter as tk
from tkinter import messagebox
from .robot_buttons import RobotButtonFrame
from .app_buttons import AppButtonFrame
from . import set_ico, _ot_2_ip
    

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
