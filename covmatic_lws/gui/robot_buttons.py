import tkinter as tk
from .button_frames import ButtonFrameBase
from ..utils import classproperty
from ..ssh import SSHClient, try_ssh
from .buttons import ColorChangingButton, ColorChangingTimerButton, SSHButtonMixin
from .images import set_ico
from ..args import Args
from .upload_protocol import ProtocolDefinition
from .log import LogWindow
from ..check_update import up_to_date
import logging
import webbrowser
import requests
import json
import os
from typing import Tuple

OT_request_headers = {"Opentrons-Version":  "2"}

class RobotButtonFrame(ButtonFrameBase):
    pass


class UpdateSystem(SSHButtonMixin, ColorChangingButton, metaclass=RobotButtonFrame.button):
    remote_dir: str = "/var/lib/jupyter/notebooks"
    system_version_file: str = "system_version.py"
    
    @property
    def logger(self):
        return logging.getLogger(type(self).__name__)
    
    @classmethod
    def current_version(cls) -> str:
        if not try_ssh():
            return ""
        with SSHClient() as client:
            client.exec_command("mkdir -p {}".format(cls.remote_dir))
            with client.scp_client() as scp_client:
                scp_client.put(*cls.paths(cls.system_version_file))
            _, stdout, _ = client.exec_command("python {}".format(cls.remote_path(cls.system_version_file)))
            s = stdout.read().decode('ascii').strip()
        return s
    
    @classproperty
    def text(self) -> str:
        return "Stations {}".format(self.current_version())
    
    def up_to_date(self):
        return up_to_date(type(self).current_version(), "covmatic-stations", python_install="python")
    
    @staticmethod
    def local_path(file: str):
        return os.path.join(os.path.dirname(__file__), file)
    
    @classmethod
    def remote_path(cls, file: str):
        return "/".join((cls.remote_dir, file))
    
    @classmethod
    def paths(cls, file: str):
        return cls.local_path(file), cls.remote_path(file)
    
    def update(self):
        self.configure(text=self.text)
        super(UpdateSystem, self).update()
    
    @property
    def state(self):
        return self.up_to_date()[0]

    def command(self):
        up2date, _, _, up_cmd = self.up_to_date()
        if not up2date:
            with SSHClient() as client:
                _, stdout, stderr = client.exec_command(up_cmd)
                for o, lvl in [
                    (stdout, "info"),
                    (stderr, "warning"),
                ]:
                    out = o.read().decode('ascii')
                    if out:
                        getattr(self.logger, lvl)(out)
        self.update()


class LightsButton(SSHButtonMixin, ColorChangingButton, metaclass=RobotButtonFrame.button):
    text = "Robot Lights"
    endpoint = ":31950/robot/lights"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(Args().ip, self.endpoint)
    
    @property
    def state(self) -> bool:
        try:
            response = requests.get(self.url, headers=OT_request_headers)
        except requests.exceptions.ConnectionError:
            state = False
        else:
            try:
                state = response.json().get("on", False)
            except json.decoder.JSONDecodeError:
                state = False
        return state
    
    @state.setter
    def state(self, value: bool):
        try:
            requests.post(self.url, json={'on': value}, headers=OT_request_headers)
        except requests.exceptions.ConnectionError:
            pass
        self.update()


class HomeButton(SSHButtonMixin, tk.Button, metaclass=RobotButtonFrame.button):
    text = "Home"
    endpoint = ":31950/robot/home"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(Args().ip, self.endpoint)
    
    def command(self):
        try:
            requests.post(self.url, json={'target': 'robot'}, headers=OT_request_headers)
        except requests.exceptions.ConnectionError:
            pass


class WinButton(ColorChangingTimerButton):
    new_win: type = None
    render: Tuple[str, tuple, dict] = ("grid", (), {})
    
    @property
    def state(self) -> bool:
        return hasattr(self, "_win") and self._win is not None and self._win.winfo_exists()
    
    @state.setter
    def state(self, value: bool):
        if self.state != value:
            if self.state:
                self._win_root.destroy()
            else:
                if hasattr(self, "_win_root") and self._win_root.winfo_exists():
                    self._win_root.destroy()
                self._win_root = tk.Toplevel()
                set_ico(self._win_root)
                self._win_root.title(type(self).text)
                self._win = type(self).new_win(self._win_root)
                self.render_win(self._win)
        self.update()
    
    def render_win(self, win):
        getattr(win, type(self).render[0])(*type(self).render[1], **type(self).render[2])
    
    def destroy(self):
        self.state = False
        super(WinButton, self).destroy()


class UploadButton(WinButton, metaclass=RobotButtonFrame.button):
    text = "Upload Protocol"
    new_win = ProtocolDefinition


class JupyterButton(SSHButtonMixin, tk.Button, metaclass=RobotButtonFrame.button):
    text = "Jupyter"
    endpoint = ":48888"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(Args().ip, self.endpoint)
    
    def command(self):
        webbrowser.open(self.url)


class RunLogButton(WinButton, metaclass=RobotButtonFrame.button):
    text = "Run Log"
    new_win = LogWindow
    render: Tuple[str, tuple, dict] = ("pack", (), dict(expand=True, fill=tk.BOTH))


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
