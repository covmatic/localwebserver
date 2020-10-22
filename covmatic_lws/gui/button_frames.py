import tkinter as tk
from .buttons import _palette, ColorChangingButton


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
                if not issubclass(c, ColorChangingButton):
                    for k, v in _palette["off"].items():
                        kwargs[k] = kwargs.get(k, v)
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


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
