import tkinter as tk
import tkinter.messagebox
import subprocess
from typing import Tuple, List
from . import _kill_app


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
        self.execute()
    
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


class OnOffSubprocessButton(ColorChangingButton, SubprocessButton):
    @SubprocessButton.state.setter
    def state(self, value: bool):
        SubprocessButton.state.fset(self, value)
        self.update()
