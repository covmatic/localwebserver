import tkinter as tk
import tkinter.filedialog
from .button_frames import ButtonFrameBase
from . import _station, _remote_protocol_file, _local_protocol_file, set_ico, get_logo, _message_lang, warningbox
from services import protocol_gen
from services.task_runner import SSHClient
from functools import partial
import os
from typing import List


class ProtocolDefinition(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super(ProtocolDefinition, self).__init__(parent, *args, **kwargs)
        self._logo_photo = get_logo(resize=0.1)
        self._logo = tk.Label(self, image=self._logo_photo)
        self._logo.grid(row=0, columnspan=2)
        
        self._left = tk.Frame(self)
        self._empty_label = tk.Label(self._left, text=" ")
        self._empty_label.grid()
        self._label = tk.Label(self._left, text="Station")
        self._label.grid()
        self._stationmenu = ProtocolDefinitionLeft(self._left)
        self._stationmenu.grid()
        
        self._ns_label = tk.Label(self._left, text="Number of Samples")
        self._ns_label.grid()
        self.ns = tk.IntVar()
        self._numsamples = tk.Entry(self._left, textvariable=self.ns)
        self._numsamples.grid()
        self._left.grid(row=1, column=0, sticky=tk.S)
        
        self._right = ProtocolDefinitionRight(self)
        self._right.grid(row=1, column=1, sticky=tk.S)
    
    def generate(self) -> str:
        if self.ns.get() <= 0:
            raise ValueError("Number of samples should be positive\nGot: {}".format(self.ns.get()))
        return protocol_gen.protocol_gen(
            self._stationmenu._buttons[0].var.get(),
            num_samples=self.ns.get(),
            language=self._right._buttons[2].var.get(),
        )


class ProtocolDefinitionLeft(ButtonFrameBase):
    pass


class ProtocolDefinitionRight(ButtonFrameBase):
    def __init__(self, parent, *args, **kwargs):
        super(ProtocolDefinitionRight, self).__init__(parent, *args, **kwargs)
        self.parent = parent


class MenuButton(tk.Menubutton):
    opts = []
    dflt = ""
    
    def __init__(self, parent, *args, **kwargs):
        self.var = tk.StringVar()
        kwargs["borderwidth"] = kwargs.get("borderwidth", 1)
        kwargs["relief"] = kwargs.get("relief", "raised")
        kwargs["indicatoron"] = kwargs.get("indicatoron", False)
        kwargs["textvariable"] = self.var
        kwargs["text"] = kwargs.get("text", self.text)
        super(MenuButton, self).__init__(parent, *args, **kwargs)
        self.menu = tk.Menu(self, tearoff=False)
        self.configure(menu=self.menu)
        
        for c in self.opts:
            self.menu.add_command(label=c, command=partial(self.var.set, c))
            if c == self.dflt:
                self.var.set(c)


class StationsMenu(MenuButton, metaclass=ProtocolDefinitionLeft.button):
    text: str = "Station"
    opts = protocol_gen._classes.keys()
    dflt = _station
    
    def __init__(self, parent, *args, **kwargs):
        kwargs["width"] = kwargs.get("width", max(19, max(map(len, protocol_gen._classes.keys()))))
        super(StationsMenu, self).__init__(parent, *args, **kwargs)


class SaveButton(metaclass=ProtocolDefinitionRight.button):
    text = "Save"
    
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
    
    @warningbox
    def command(self):
        s = self.parent.parent.generate()
        with tk.filedialog.asksaveasfile(title="Save Protocol", defaultextension=".py", filetypes=(("python scripts", "*.py"),)) as f:
            f.write(s)


class UploadButton(metaclass=ProtocolDefinitionRight.button):
    text = "Upload"
    
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
    
    @warningbox
    def command(self):
        if not os.path.exists(os.path.dirname(_local_protocol_file)):
            os.makedirs(os.path.dirname(_local_protocol_file))
        with open(_local_protocol_file, "w") as f:
            f.write(self.parent.parent.generate())
        with SSHClient() as client:
            client.exec_command("mkdir -p {}".format(os.path.dirname(_remote_protocol_file)))
            with client.scp_client() as scp_client:
                scp_client.put(_local_protocol_file, _remote_protocol_file)


class LangMenu(MenuButton, metaclass=ProtocolDefinitionRight.button):
    text: str = "Language"
    opts: List[str] = sorted(["ENG", "ITA"])
    dflt: str = _message_lang


if __name__ == "__main__":
    root = tk.Tk()
    set_ico(root)
    root.title('Upload Protocol')
    win = ProtocolDefinition(root)
    win.grid()
    root.mainloop()
