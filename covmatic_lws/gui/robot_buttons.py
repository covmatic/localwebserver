import tkinter as tk
from .button_frames import ButtonFrameBase
from ..utils import classproperty
from ..ssh import SSHClient, try_ssh
from .buttons import ColorChangingButton, ColorChangingTimerButton, SSHButtonMixin
from .images import set_ico
from ..args import Args
from .upload_protocol import ProtocolDefinition
import logging
import webbrowser
import requests
import json
import os


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
        return "System9 {}".format(self.current_version())
    
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
    
    @staticmethod
    def pypi_index():
        s = os.environ.get("SYSTEM9_INDEX", "https://test.pypi.org/pypi/")
        return s and " -i {}".format(s)
    
    @staticmethod
    def latest_version() -> str:
        pkg_name = "covid19-system9"
        for s in os.popen("{} -m pip search{} -V {}".format(os.sys.executable, UpdateSystem.pypi_index(), pkg_name)).read().split("\n"):
            if s[:len(pkg_name)] == pkg_name:
                return s.split("(")[1].split(")")[0]
        return UpdateSystem.current_version()
    
    @property
    def state(self):
        return self.current_version() == self.latest_version()

    def command(self):
        if not self.state:
            with SSHClient() as client:
                _, stdout, stderr = client.exec_command("python -m pip install{} covid19-system9 --upgrade".format(self.pypi_index()))
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
            response = requests.get(self.url)
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
            requests.post(self.url, json={'on': value})
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
            requests.post(self.url, json={'target': 'robot'})
        except requests.exceptions.ConnectionError:
            pass


class UploadButton(ColorChangingTimerButton, metaclass=RobotButtonFrame.button):
    text = "Upload Protocol"
    
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
                self._win_root.title('Upload Protocol')
                self._win = ProtocolDefinition(self._win_root)
                self._win.grid()
        self.update()
    
    def destroy(self):
        self.state = False
        super(UploadButton, self).destroy()


class JupyterButton(SSHButtonMixin, tk.Button, metaclass=RobotButtonFrame.button):
    text = "Jupyter"
    endpoint = ":48888"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(Args().ip, self.endpoint)
    
    def command(self):
        webbrowser.open(self.url)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
