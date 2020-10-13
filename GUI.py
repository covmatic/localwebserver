import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
import subprocess
import os
import webbrowser
import requests
from typing import Tuple, List


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
        self._robot_buttons.grid(row=1, column=0, sticky=tk.N)
        self._app_buttons.grid(row=1, column=1, sticky=tk.N)


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


class ColorChangingButton(tk.Button):
    def __init__(self, parent, bg: Tuple[str, str] = ('#9a9ba0', '#dedfe5'), activebackground: Tuple[str, str] = ('#c5c6cc', '#ffffff'), *args, **kwargs):
        super(ColorChangingButton, self).__init__(parent, *args, **kwargs)
        self._bg = bg
        self._activebackground = activebackground
        self.update()
    
    def update(self):
        s = self.state
        self.configure(bg=self._bg[s], activebackground=self._activebackground[s])
    
    def command(self):
        self.state = not self.state


class RobotButtonFrame(ButtonFrameBase):
    pass


class LightsButton(ColorChangingButton, metaclass=RobotButtonFrame.button):
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


class SubprocessButton(tk.Button):
    def __init__(self, parent, kill_app: bool = _kill_app, *args, **kwargs):
        super(SubprocessButton, self).__init__(parent, *args, **kwargs)
        self._kill_app = kill_app
        self._subprocess = None
    
    def __del__(self):
        if self._kill_app and self.state:
            self._subprocess.kill()
    
    @property
    def state(self) -> bool:
        if self._subprocess is not None:
            self._subprocess.poll()
            if self._subprocess.returncode is None:
                return True
            else:
                self._subprocess = None
        return False
    
    @state.setter
    def state(self, value: bool):
        if self.state != value:
            if self.state:
                self._subprocess.kill()
                self._subprocess = None
            else:
                self.execute()
    
    def check_app(self) -> bool:
        return True
    
    def command(self):
        self.state = not self.state
    
    def execute(self):
        if self.check_app():
            if self.state:
                    tk.messagebox.showwarning(*self._already_running)
            else:
                self._subprocess = subprocess.Popen(self._subprocess_args)
        else:
            tk.messagebox.showwarning(*self._check_fail)
    
    _already_running: str = ""
    _check_fail: Tuple[str, str] = "", ""
    _subprocess_args: List[str] = []


class OnOffSubprocessButton(ColorChangingButton, SubprocessButton):
    @SubprocessButton.state.setter
    def state(self, value: bool):
        SubprocessButton.state.fset(self, value)
        self.update()


class OpentronsButton(OnOffSubprocessButton, metaclass=AppButtonFrame.button):
    text: str = "Opentrons APP"
    endpoint = ":5001/api/check"
    
    @property
    def url(self) -> str:
        return "http://127.0.0.1{}".format(self.endpoint)
    
    def __init__(self, parent, app_file: str = _opentrons_app, *args, **kwargs):
        self._app_file = app_file 
    
    def check_app(self) -> bool:
        return os.path.exists(self._app_file) and os.path.isfile(self._app_file)
    
    _already_running: str = "Opentrons APP running", "Another instance of the Opentrons APP has already been launched"
    
    @property
    def _check_fail(self) -> Tuple[str, str]:
        return "Opentrons APP not found", "Opentrons APP not found at {}\nPlease set the correct path in the environment variable:\n\nOPENTRONS_APP".format(self._app_file)
    
    @property
    def _subprocess_args(self) -> List[str]:
        return [self._app_file]
        

class StartRunButton(metaclass=AppButtonFrame.button):
    text: str = "Start a New Run"
    
    def command(self, app_url: str = _web_app):
        webbrowser.open(app_url)


class ServerButton(OnOffSubprocessButton, metaclass=AppButtonFrame.button):
    text: str = "Local Web Server"
    
    def __init__(self, parent, python_exe: str = os.sys.executable, python_script: str = "./app.py", *args, **kwargs):
        self._python = python_exe
        self._script = python_script
    
    def check_app(self) -> bool:
        return os.path.exists(self._python) and os.path.isfile(self._python) and os.path.exists(self._script) and os.path.isfile(self._script)
    
    _already_running: str = "LocalWebServer running", "Another instance of the LocalWebServer has already been launched"\
    
    @property
    def _check_fail(self) -> Tuple[str, str]:
        return "LocalWebServer not found", "LocalWebServer files not found (one or more):\n\n{}\n{}".format(self._python, self._script)\
    
    @property
    def _subprocess_args(self) -> List[str]:
        return [self._python, self._script]


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
