import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
import subprocess
import os
import webbrowser
import requests
from typing import Tuple


_ot_2_ip: str = os.environ.get("OT2IP", "")
_icon_file: str = os.environ.get("ICON_FILE", "./Covmatic_Icon.jpg")
_icon_url: str = os.environ.get("ICON_URL", "https://covmatic.org/wp-content/uploads/2020/10/cropped-Favicon-180x180.jpg")
_opentrons_app: str = os.environ.get("OPENTRONS_APP", "C:/Program Files/Opentrons/Opentrons.exe")
_web_app: str = os.environ.get("WEB_APP_URL", "https://ec2-15-161-32-20.eu-south-1.compute.amazonaws.com/stations")
_kill_app: bool = True


def set_ico(parent, url: str = _icon_url, file: str = _icon_file):
    if not os.path.exists(file):
        os.system("wget {} -O {}".format(url, file))
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
        self._robot_buttons.grid(row=1, column=0)
        self._app_buttons.grid(row=1, column=1)


class ButtonsFrameMeta(type):
    class ButtonMeta(type):
        def __new__(cls, name, bases, classdict):
            c = super(ButtonsFrameMeta.ButtonMeta, cls).__new__(cls, name, bases, classdict)
            
            text = getattr(c, "text", None)
            _init = classdict.get("__init__", None)
            
            def init(self, parent, text: str = text, command: str = "command", *args, **kwargs):
                if text:
                    kwargs["text"] = text
                if command:
                    kwargs["command"] = getattr(self, command, None)
                super(c, self).__init__(parent, *args, **kwargs)
                if _init is not None:
                    _init(self, parent, *args, **kwargs)
                
            c.__init__ = init
            return c
    
    def __init__(cls, name, bases, classdict):
        super(ButtonsFrameMeta, cls).__init__(name, bases, classdict)
        cls.buttons = []
    
    def button(cls, name, bases, classdict):
        cls.buttons.append(cls.ButtonMeta(name, bases or (tk.Button,), classdict))
        return cls.buttons[-1]


class ButtonFrameBase(tk.Frame, metaclass=ButtonsFrameMeta):
    def __init__(self, parent, *args, **kwargs):
        super(ButtonFrameBase, self).__init__(parent, *args, **kwargs)
        self._buttons = []
        for i, B in enumerate(type(self).buttons):
            self._buttons.append(B(self))
            self._buttons[i].grid(row=i, sticky=tk.N+tk.S+tk.E+tk.W)


class RobotButtonFrame(ButtonFrameBase):
    pass


class LightsButton(metaclass=RobotButtonFrame.button):
    text = "Robot Lights"
    endpoint = ":31950/robot/lights"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(_ot_2_ip, self.endpoint)
    
    @property
    def state(self) -> bool:
        try:
            state = requests.get(self.url).json().get("on", False)
        except requests.exceptions.ConnectionError:
            state = False
        return state
    
    @state.setter
    def state(self, value: bool):
        try:
            requests.post(self.url, json={'on': value})
        except requests.exceptions.ConnectionError:
            pass
        self.update()
    
    def command(self):
        self.state = not self.state
    
    def update(self):
        s = self.state
        self.configure(bg=self._bg[s], activebackground=self._activebackground[s])
    
    def __init__(self, parent, bg: Tuple[str, str] = ('#9a9ba0', '#dedfe5'), activebackground: Tuple[str, str] = ('#c5c6cc', '#ffffff'), *args, **kwargs):
        self._bg = bg
        self._activebackground = activebackground
        self.update()


class HomeButton(metaclass=RobotButtonFrame.button):
    text = "Home"
    endpoint = ":31950/robot/home"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(_ot_2_ip, self.endpoint)
    
    def command(self):
        try:
            requests.post(self.url, json={'target': 'robot'})
        except requests.exceptions.ConnectionError:
            pass


class AppButtonFrame(ButtonFrameBase):
    pass


class OpentronsButton(metaclass=AppButtonFrame.button):
    text: str = "Launch Opentrons APP"
    
    def __init__(self, parent, kill_app: bool = _kill_app, *args, **kwargs):
        self._kill_app = kill_app
        self._subprocess = None
    
    def __del__(self):
        if self._kill_app and self.subprocess_running():
            self._subprocess.kill()
    
    def subprocess_running(self) -> bool:
        if self._subprocess is not None:
            self._subprocess.poll()
            if self._subprocess.returncode is None:
                return True
            else:
                self._subprocess = None
        return False
    
    def command(self, app_file: str = _opentrons_app):
        if os.path.exists(app_file) and os.path.isfile(app_file):
            if self.subprocess_running():
                    tk.messagebox.showwarning("Opentrons APP running", "Another instance of the Opentrons APP has already been launched")
            else:
                self._subprocess = subprocess.Popen(app_file)
        else:
            tk.messagebox.showwarning("Opentrons APP not found", "Opentrons APP not found at {}\nPlease set the correct path in the environment variable:\n\nOPENTRONS_APP".format(app_file))


class StartRunButton(metaclass=AppButtonFrame.button):
    text: str = "Start a New Run"
    
    def command(self, app_url: str = _web_app):
        webbrowser.open(app_url)


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
