import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import socket
from .button_frames import ButtonFrameBase
from .buttons import SSHButtonMixin, ConnectionLabel, _palette
from .images import set_ico, get_logo
from .utils import warningbox
from ..ssh import SSHClient, try_ssh
from ..args import Args
from .. import protocol_gen
from functools import partial
import os
from scp import SCPException
import json
from typing import List
from ..utils import SingletonMeta, classproperty
from itertools import chain
import time


class ProtocolDefinition(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super(ProtocolDefinition, self).__init__(parent, *args, **kwargs)
        self._logo_photo = get_logo(resize=0.1)
        self._logo = tk.Label(self, image=self._logo_photo)
        self._ip_label = tk.Label(self, text=Args().ip)
        self._logo.grid(row=0, columnspan=2)
        self._ip_label.grid(row=1, columnspan=2)
        self._conn_label = ConnectionLabel(self)
        self._conn_label.grid(row=2, columnspan=2)
        
        self._left = ParentFrame(self)
        self._station_menu = StationsMenu(self._left, **_palette["off"])
        self._argframe = ArgFrame(self._left, station_var=self._station_menu.var)
        self._station_menu.var.trace_add("write", self._argframe.update)
        self._station_menu.var.trace_add("write", lambda *args, **kwargs: setattr(Args(), "station", self._station_menu.var.get()))
        self._station_menu.grid()
        self._argframe.grid()
        self._argframe.update()
        self._left.grid(row=3, column=0, sticky=tk.E+tk.W+tk.S)
        
        self._right = ProtocolDefinitionRight(self)
        self._right.grid(row=3, column=1, sticky=tk.S)
        self._right._buttons[2].var.trace_add("write", self.protocol_changed)
        
        self._tiplog_box = TipLog(self)
        self._tiplog_box.grid(row=4, columnspan=2, sticky=tk.E+tk.W)
        self._validfile = False
    
    @property
    def file_is_valid(self) -> bool:
        return self._validfile
    
    def protocol_changed(self, *args, **kwargs):
        self._validfile = False
    
    def protocol_saved(self, *args, **kwargs):
        self._validfile = True
    
    @property
    def ns(self) -> int:
        return self._argframe.as_dict()["num_samples"]
    
    def generate(self) -> str:
        return protocol_gen.protocol_gen(
            self._station_menu.var.get(),
            **self._argframe.as_dict(allow_none=False),
            language=self._right._buttons[2].var.get(),
            wait_first_log=Args().wait_log,
        )


class HasParentMixin:
    def __init__(self, parent, *args, **kwargs):
        super(HasParentMixin, self).__init__(parent, *args, **kwargs)
        self.parent = parent


class ParentFrame(HasParentMixin, tk.Frame):
    pass


class ArgFrame(ParentFrame):
    def __init__(self, parent, station_var: tk.StringVar, *args, **kwargs):
        super(ArgFrame, self).__init__(parent, *args, **kwargs)
        self._station = station_var
        
        self._vars = None
        self._labels = None
        self._entries = None
    
    def __iter__(self):
        return ((v.key, v.check_get()) for v in (self._vars or []))
    
    def as_dict(self, allow_none = True):
        args = [(key, value) for (key, value) in iter(self) if value is not None or allow_none]
        return dict(args)
    
    def update(self, *args, **kwargs):
        for v in chain(self._labels or [], self._entries or []):
            v.destroy()
        del self._vars
        del self._labels 
        del self._entries
        self._vars = []
        self._labels = []
        self._entries = []
        for Arg in protocol_gen._classes.get(self._station.get(), [])[2:]:
            self._vars.append(Arg())
            self._vars[-1].trace_add("write", self.parent.parent.protocol_changed)
            self._labels.append(tk.Label(self, text=self._vars[-1].verbose_name))
            self._labels[-1].grid()
            self._entries.append(tk.Entry(self, textvariable=self._vars[-1]))
            self._entries[-1].grid()
        self._labels.append(tk.Label(self, text="Next tips"))
        self._labels[-1].grid()
        self.parent.parent.protocol_changed()
        super(ArgFrame, self).update()


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


class StationsMenu(MenuButton):
    text: str = "Station"
    opts = protocol_gen._classes.keys()
    
    @classproperty
    def dflt(cls) -> str:
        return Args().station
    
    def __init__(self, parent, *args, **kwargs):
        kwargs["width"] = kwargs.get("width", max(19, max(map(len, protocol_gen._classes.keys()))))
        super(StationsMenu, self).__init__(parent, *args, **kwargs)


class NumSamples(int, metaclass=SingletonMeta):
    pass


class ProtocolDefinitionRight(ParentFrame, ButtonFrameBase):
    pass


class SaveButton(HasParentMixin, tk.Button, metaclass=ProtocolDefinitionRight.button):
    text = "Save"
    
    @warningbox
    def command(self):
        s = self.parent.parent.generate()
        fname = tk.filedialog.asksaveasfilename(title="Save Protocol", defaultextension=".py", filetypes=(("python scripts", "*.py"),))
        if fname:
            Args().protocol_local = fname
            with open(Args().protocol_local, "w") as f:
                f.write(s)
                self.parent.parent.protocol_saved()


class UploadButton(HasParentMixin, SSHButtonMixin, tk.Button, metaclass=ProtocolDefinitionRight.button):
    last_n = None
    text = "Upload"
    
    @warningbox
    def command(self):
        s = self.parent.parent.generate()
        if not os.path.exists(os.path.dirname(Args().protocol_local)):
            os.makedirs(os.path.dirname(Args().protocol_local))
        generate = not (self.parent.parent.file_is_valid and os.path.exists(Args().protocol_local))
        if generate:
            with open(Args().protocol_local, "w") as f:
                f.write(s)
                self.parent.parent.protocol_saved()
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
        if try_ssh():
            with SSHClient() as client:
                client.exec_command("rm -f {}".format(Args().tip_log_remote))
        self.update()
    
    @property
    def tip_log(self) -> str:
        os.makedirs(os.path.dirname(Args().tip_log_local), exist_ok=True)
        s = ""
        if try_ssh():
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


class TipLogResetButton(SSHButtonMixin, tk.Button, metaclass=ProtocolDefinitionRight.button):
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
