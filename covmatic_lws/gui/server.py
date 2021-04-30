from typing import Optional
import tkinter as tk
import tkinter.simpledialog
from functools import partial
from threading import Thread, Timer, Lock
import cherrypy
from ..args import Args
from .utils import warningbox
from ..utils import SingletonMeta


# Configuration for the GUI server;
# keep in mind it will:
# - receive log from OT2
# - receive barcode calls for barcode dialogs
#
DEFAULT_CONFIG = {
    "global": {
        "server.socket_host": "::",
        "server.socket_port": Args().barcode_port,
        "engine.autoreload.on": False,
    }
}


class LogContent(tk.StringVar, metaclass=SingletonMeta):
    lock = Lock()


class GUIServer:
    def __init__(self, parent, config: Optional[dict] = DEFAULT_CONFIG):
        super(GUIServer, self).__init__()
        self._parent = parent
        self._config = config
    
    @warningbox
    def barcode(self, action: str) -> str:
        root = tk.Tk()
        root.withdraw()
        s = ""
        try:
            s = tk.simpledialog.askstring("Barcode", "Scan {}ing barcode".format(action), parent=root)
        finally:
            root.destroy()
        return s
    
    @cherrypy.expose
    def enter(self):
        return self.barcode("enter")
    
    @cherrypy.expose
    def exit(self):
        return self.barcode("exit")
    
    @cherrypy.expose
    def reset_log(self):
        LogContent().set("")
    
    @cherrypy.expose
    def log(self):
        s = cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length']))
        try:
            s = s.decode('utf-8')
        except UnicodeDecodeError:
            s = s.decode('ascii')
        with LogContent.lock:
            LogContent().set("{}{}{}".format(LogContent().get(), "\n" if LogContent().get() else "", s))
    
    @staticmethod
    def stop():
        cherrypy.engine.exit()


class GUIServerThread(GUIServer, Thread):    
    def run(self):
        cherrypy.quickstart(self, config=self._config)
    
    def join(self, timeout=None, after: float = 0):
        if after > 0:
            Timer(after, partial(self.join, timeout=timeout)).start()
        else:
            self.stop()
            super(GUIServerThread, self).join(timeout=timeout)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
