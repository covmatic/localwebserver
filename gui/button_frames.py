import tkinter as tk


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
