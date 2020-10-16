from typing import Optional
import tkinter as tk
import tkinter.simpledialog
from functools import partialmethod, partial
from threading import Thread, Timer
import cherrypy
from .args import Args
from .utils import warningbox


DEFAULT_CONFIG = {
    "global": {
        "server.socket_host": "0.0.0.0",
        "server.socket_port": Args().barcode_port,
        "engine.autoreload.on": False,
    }
}


class BarcodeServer:
    def __init__(self, parent, config: Optional[dict] = DEFAULT_CONFIG):
        super(BarcodeServer, self).__init__()
        self._parent = parent
        self._config = config
    
    @warningbox
    def barcode(self, action: str) -> str:
        root = tk.Tk()
        root.withdraw()
        s = ""
        try:
            s = tk.simpledialog.askstring("Barcode", "Scan barcode of {}ing rack".format(action), parent=root)
        finally:
            root.destroy()
        return s
    
    @cherrypy.expose
    def enter(self):
        return self.barcode("enter")
    
    @cherrypy.expose
    def exit(self):
        return self.barcode("exit")
    
    @staticmethod
    def stop():
        cherrypy.engine.exit()


class BarcodeServerThread(BarcodeServer, Thread):    
    def run(self):
        cherrypy.quickstart(self, config=self._config)
    
    def join(self, timeout=None, after: float = 0):
        if after > 0:
            Timer(after, partial(self.join, timeout=timeout)).start()
        else:
            self.stop()
            super(BarcodeServerThread, self).join(timeout=timeout)
