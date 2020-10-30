import tkinter as tk
from .server import LogContent, GUIServerThread
from .buttons import ConnectionLabel
from .images import set_ico, get_logo
from ..args import Args
import os


class LogWindow(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super(LogWindow, self).__init__(parent, *args, **kwargs)
        self._logo_photo = get_logo(resize=0.1)
        self._logo = tk.Label(self, image=self._logo_photo)
        self._ip_label = tk.Label(self, text=Args().ip)
        self._conn_label = ConnectionLabel(self)
        self._logo.pack()
        self._ip_label.pack()
        self._conn_label.pack()
        
        self._scrollbar = tk.Scrollbar(self)
        self._text = tk.Text(self, width=128)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self._scrollbar.config(command=self._text.yview)
        self._text.config(yscrollcommand=self._scrollbar.set)
        self._cbname = LogContent(self).trace_add("write", self.update)
        
        if __name__ == "__main__":
            self._gui_server = GUIServerThread(self)
            self._gui_server.start()
        self.update()
        self._text.see(tk.END)
    
    def update(self, *args, **kwargs):
        scroll = self._scrollbar.get()[1] == 1
        self._text.replace("1.0", tk.END, LogContent().get())
        if scroll:
            self._text.see(tk.END)
        super(LogWindow, self).update()
    
    def destroy(self):
        super(LogWindow, self).destroy()
        LogContent().trace_remove("write", self._cbname)


if __name__ == "__main__":
    root = tk.Tk()
    set_ico(root)
    root.title('Run Log')
    win = LogWindow(root)
    # win.grid(sticky=tk.N+tk.E+tk.S+tk.W)
    win.pack(expand=True, fill=tk.BOTH)
    root.mainloop()
    os.kill(os.getpid(), 9)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
