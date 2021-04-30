import tkinter as tk
import tkinter.messagebox
import subprocess
from typing import Tuple, List
from . import _kill_app
from ..ssh import try_ssh

_palette = {
    "off": {
        "bg": "#fafafa",
        "activebackground": "#ffffff",
        "fg": "black",
        "activeforeground": "black",
    },
    "on": {
        "bg": "#0477FC",
        "activebackground": "#318ff9",
        "fg": "white",
        "activeforeground": "white",
    }
}


class SSHButtonMixin:
    def __init__(self, *args, **kwargs):
        super(SSHButtonMixin, self).__init__(*args, **kwargs)
        if not try_ssh():
            self.config(state=tk.DISABLED)


class SubprocessButton(tk.Button):
    def __init__(self, parent, kill_app: bool = _kill_app, *args, **kwargs):
        super(SubprocessButton, self).__init__(parent, *args, **kwargs)
        self._kill_app = kill_app
        self._subprocess = None
    
    def destroy(self):
        if self._kill_app and self.state:
            self._subprocess.kill()
            self._subprocess = None
        super(SubprocessButton, self).destroy()
    
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
    
    _already_running: str = ("", "")
    _check_fail: Tuple[str, str] = ("", "")
    _subprocess_args: List[str] = []


class ColorChangingButton(tk.Button):
    def __init__(
        self,
        parent,
        bg: Tuple[str, str] = (_palette["off"]["bg"], _palette["on"]["bg"]),
        activebackground: Tuple[str, str] = (_palette["off"]["activebackground"], _palette["on"]["activebackground"]),
        fg: Tuple[str, str] = (_palette["off"]["fg"], _palette["on"]["fg"]),
        activeforeground: Tuple[str, str] = (_palette["off"]["activeforeground"], _palette["on"]["activeforeground"]),
        *args,
        **kwargs
    ):
        super(ColorChangingButton, self).__init__(parent, *args, **kwargs)
        self._bg = bg
        self._activebackground = activebackground
        self._fg = fg
        self._activeforeground = activeforeground
        self.update()
    
    def update(self):
        s = self.state
        self.configure(bg=self._bg[s], activebackground=self._activebackground[s], fg=self._fg[s], activeforeground=self._activeforeground[s])
    
    def command(self):
        self.state = not self.state


class OnOffSubprocessButton(ColorChangingButton, SubprocessButton):
    @SubprocessButton.state.setter
    def state(self, value: bool):
        SubprocessButton.state.fset(self, value)
        self.update()


class ColorChangingTimerButton(ColorChangingButton):
    def __init__(self, parent, interval: float = 1, *args, **kwargs):
        super(ColorChangingTimerButton, self).__init__(parent, *args, **kwargs)
        self._interval = interval
        self._loop()

    def _loop(self):
        self.update()
        self.after(int(self._interval*1000), self._loop)
    
    def update_thread(self):
        self.update()
    
    def destroy(self):
        super(ColorChangingTimerButton, self).destroy()


class ColorChangingSubprocessButton(ColorChangingTimerButton, SubprocessButton):
    def command(self):
        self.execute()
        self.update()


class ConnectionLabel(tk.Label):
    def __init__(self, parent, text=None, *args, **kwargs):
        if text is None:
            text = " " if try_ssh() else "(disconnected)"
        super(ConnectionLabel, self).__init__(parent, *args, text=text, **kwargs)
        

# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
