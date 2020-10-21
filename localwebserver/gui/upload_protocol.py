import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
from .button_frames import ButtonFrameBase
from .images import set_ico, get_logo
from .utils import warningbox
from ..ssh import SSHClient
from ..args import Args
from services import protocol_gen
from functools import partial
import os
from scp import SCPException
import json
from typing import List
from api.utils import SingletonMeta


class ProtocolDefinition(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super(ProtocolDefinition, self).__init__(parent, *args, **kwargs)
        self._logo_photo = get_logo(resize=0.1)
        self._logo = tk.Label(self, image=self._logo_photo)
        self._ip_label = tk.Label(self, text=Args().ip)
        self._logo.grid(row=0, columnspan=2)
        self._ip_label.grid(row=1, columnspan=2)
        
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
        
        self._tiplog_label = tk.Label(self._left, text="Next tips")
        self._tiplog_label.grid()
        self._left.grid()
        
        self._right = ProtocolDefinitionRight(self)
        self._right.grid(row=2, column=1, sticky=tk.S)
        
        self._tiplog_box = TipLog(self)
        self._tiplog_box.grid(row=3, columnspan=2, sticky=tk.E+tk.W)
    
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
    dflt = Args().station
    
    def __init__(self, parent, *args, **kwargs):
        kwargs["width"] = kwargs.get("width", max(19, max(map(len, protocol_gen._classes.keys()))))
        super(StationsMenu, self).__init__(parent, *args, **kwargs)


class NumSamples(int, metaclass=SingletonMeta):
    pass


class SaveButton(metaclass=ProtocolDefinitionRight.button):
    text = "Save"
    
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
    
    @property
    def ns(self) -> int:
        return self.parent.parent.ns.get()
    
    @warningbox
    def command(self):
        s = self.parent.parent.generate()
        fname = tk.filedialog.asksaveasfilename(title="Save Protocol", defaultextension=".py", filetypes=(("python scripts", "*.py"),))
        if fname:
            Args().protocol_local = fname
            with open(Args().protocol_local, "w") as f:
                f.write(s)
                NumSamples.reset(self.ns)


class UploadButton(metaclass=ProtocolDefinitionRight.button):
    last_n = None
    text = "Upload"
    
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
    
    @property
    def ns(self) -> int:
        return self.parent.parent.ns.get()
    
    @warningbox
    def command(self):
        s = self.parent.parent.generate()
        if not os.path.exists(os.path.dirname(Args().protocol_local)):
            os.makedirs(os.path.dirname(Args().protocol_local))
        generate = not os.path.exists(Args().protocol_local) or NumSamples() != self.ns
        if generate:
            with open(Args().protocol_local, "w") as f:
                f.write(s)
            NumSamples.reset(self.ns)
        with SSHClient() as client:
            client.exec_command("mkdir -p {}".format(os.path.dirname(Args().protocol_remote)))
            with client.scp_client() as scp_client:
                scp_client.put(Args().protocol_local, Args().protocol_remote)
            tk.messagebox.showinfo("Uploaded", (
                "Generated new protocol:\n{}\n\nUploaded to\n{}"
                if generate else
                "Loaded protocol from disk:\n{}\n\nUploaded to\n{}"
            ).format(Args().protocol_local, Args().protocol_remote))


class LangMenu(MenuButton, metaclass=ProtocolDefinitionRight.button):
    text: str = "Language"
    opts: List[str] = sorted(["ENG", "ITA"])
    dflt: str = Args().lang


class TipLog(tk.Text):
    def __init__(self, parent, height=8, width=24, state=tk.DISABLED, **kwargs):
        super(TipLog, self).__init__(parent, height=height, width=width, state=state, **kwargs)
        self.update()
    
    @warningbox
    def reset(self):
        with SSHClient() as client:
            client.exec_command("rm -f {}".format(Args().tip_log_remote))
        self.update()
    
    @property
    def tip_log(self) -> str:
        s = ""
        try:
            with SSHClient() as client:
                with client.scp_client() as scp_client:
                    scp_client.get(Args().tip_log_remote, Args().tip_log_local)
        except SCPException as e:
            s = "tip log not found\nstarting from the beginning"
        else:
            with open(Args().tip_log_local, "r") as f:
                j = json.load(f)
            s = "\n\n".join("{}\n{}".format(k.replace("_", " ").strip(), v) for k, v in j.get("next", {}).items())
        return s
    
    def update(self):
        self.config(state=tk.NORMAL)
        self.delete(1.0, "end")
        self.insert(1.0, self.tip_log)
        super(TipLog, self).update()
        self.config(state=tk.DISABLED)


class TipLogResetButton(metaclass=ProtocolDefinitionRight.button):
    text: str = "Reset Tips"
    
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
    
    def command(self):
        self.parent.parent._tiplog_box.reset()


if __name__ == "__main__":
    root = tk.Tk()
    set_ico(root)
    root.title('Upload Protocol')
    win = ProtocolDefinition(root)
    win.grid()
    root.mainloop()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
