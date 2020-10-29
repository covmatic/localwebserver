import tkinter as tk
from ..args import Args
from .robot_buttons import RobotButtonFrame
from .app_buttons import AppButtonFrame
from .images import get_logo
from .server import GUIServerThread, LogContent
from .buttons import ConnectionLabel


class Covmatic(tk.Frame):
    def __init__(self,
        parent: tk.Tk,
        *args, **kwargs
    ):
        super(Covmatic, self).__init__(parent, *args, **kwargs)
        LogContent(self)
        self._ip_label = tk.Label(self, text=Args().ip)
        self._empty_label = ConnectionLabel(self)
        self._logo_photo = get_logo(resize=0.1)
        self._logo = tk.Label(self, image=self._logo_photo)
        self._robot_buttons = RobotButtonFrame(self)
        self._app_buttons = AppButtonFrame(self)
        
        self._logo.grid(row=0, columnspan=2)
        self._ip_label.grid(row=1, columnspan=2)
        self._empty_label.grid(row=2, columnspan=2)
        self._robot_buttons.grid(row=3, column=0, sticky=tk.N)
        self._app_buttons.grid(row=3, column=1, sticky=tk.N)
        self._gui_server = GUIServerThread(self)
        self._gui_server.start()
    
    def destroy(self):
        super(Covmatic, self).destroy()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
