"""Tempdeck GUI"""
from ..args import Args
import tkinter as tk
import tkinter.messagebox
from serial.tools.list_ports import comports
from .images import set_ico, get_logo
from .utils import warningbox
from .buttons import _palette
from opentrons.drivers.temp_deck import TempDeck


class TempDeckContext(TempDeck):
    def __init__(self, port, *args, **kwargs):
        super(TempDeckContext, self).__init__(*args, **kwargs)
        self._port = port
    
    def __enter__(self):
        self.connect(self._port)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_connected():
            self.disconnect()
        return exc_val is None


class RangedInt(tk.IntVar):
    def __init__(self, parent, min=0, max=127, *args, **kwargs):
        super(RangedInt, self).__init__(parent, *args, **kwargs)
        self._min = min
        self._max = max
    
    @property
    def ok(self) -> bool:
        return self._min <= self.get() <= self._max        


class TempDeckGUI(tk.Frame):
    def __init__(self, parent, default_temp: int = 55, pid_tempdeck: int = 61075, *args, **kwargs):
        super(TempDeckGUI, self).__init__(parent, *args, **kwargs)
        self._pid_tempdeck = pid_tempdeck
        self._temp = RangedInt(self, min=4, max=95, value=default_temp)
        self._logo_photo = get_logo(resize=0.1)
        
        self._logo = tk.Label(self, image=self._logo_photo)
        self._empty_label = tk.Label(self, text=" ")
        
        self._label = tk.Label(self, text="Temperature")
        self._entry = tk.Entry(self, textvariable=self._temp, width=3)
        self._butt = tk.Button(self, text="Set", width=5, command=self.set_temp, **_palette["off"])
        self._deac = tk.Button(self, text="Deactivate", command=self.deactivate, **_palette["off"])
        self._refresh = tk.Button(self, text="Refresh", command=self.scan, **_palette["off"])
        
        self._logo.grid(row=0, columnspan=3)
        self._empty_label.grid(row=1, columnspan=3)
        self._label.grid(row=2, column=0, columnspan=1, sticky=tk.W+tk.E)
        self._entry.grid(row=2, column=1, columnspan=2, sticky=tk.W+tk.E)
        self._refresh.grid(row=3, column=0, sticky=tk.W+tk.E)
        self._butt.grid(row=3, column=1, sticky=tk.W+tk.E)
        self._deac.grid(row=3, column=2, sticky=tk.W+tk.E)
        self.grid()
        
        self._ports = []
        self.scan()
    
    @warningbox
    def deactivate(self):
        for p in self._ports:
            with TempDeckContext(p) as td:
                td.deactivate()
    
    @warningbox
    def set_temp(self):
        if self._temp.ok:
            # tk.messagebox.showinfo("Temperature", "Setting temperature to {}°C".format(self._temp.get()))
            for p in self._ports:
                with TempDeckContext(p) as td:
                    td.start_set_temperature(self._temp.get())
        else:
            tk.messagebox.showwarning("Temperature", "Invalid temperature: {}°C\n\nTemperature must be between {}°C and {}°C".format(self._temp.get(), self._temp._min, self._temp._max))
    
    def scan(self):
        self._ports = [p.device for p in comports() if p.pid == self._pid_tempdeck]
        (tk.messagebox.showinfo if self.n_devices else tk.messagebox.showwarning)("Scan", "Found {} tempdeck{}".format(self.n_devices, ("s", "")[self.n_devices == 1]))
    
    @property
    def n_devices(self) -> int:
        return len(self._ports)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Covmatic TempDeck")
    set_ico(root, "Covmatic_Icon_Red")
    td = TempDeckGUI(root)
    root.mainloop()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
