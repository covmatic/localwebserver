import tkinter as tk
from .button_frames import ButtonFrameBase, classproperty
from .buttons import ColorChangingButton, ColorChangingTimerButton
from . import _ot_2_ip, set_ico
from .upload_protocol import ProtocolDefinition
from services.task_runner import SSHClient
import webbrowser
import requests
import json
import os


class RobotButtonFrame(ButtonFrameBase):
    pass


class UpdateSystem(ColorChangingButton, metaclass=RobotButtonFrame.button):
    remote_dir: str = "/var/lib/jupyter/notebooks"
    system_version_file: str = "system_version.py"
    
    @classmethod
    def current_version(cls) -> str:
        with SSHClient() as client:
            client.exec_command("mkdir -p {}".format(cls.remote_dir))
            with client.scp_client() as scp_client:
                scp_client.put(*cls.paths(cls.system_version_file))
            _, stdout, _ = client.exec_command("python {}".format(cls.remote_path(cls.system_version_file)))
            s = stdout.read().decode('ascii').strip()
        return s
    
    @classproperty
    def text(self) -> str:
        return "System9 v{}".format(self.current_version())
    
    @staticmethod
    def local_path(file: str):
        return os.path.join(os.path.dirname(__file__), file)
    
    @classmethod
    def remote_path(cls, file: str):
        return os.path.join(cls.remote_dir, file)
    
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
                _, sdtout, _ = client.exec_command("python -m pip install{} covid19-system9 --upgrade".format(self.pypi_index()))
                sdtout.read()
        self.update()


class LightsButton(ColorChangingButton, metaclass=RobotButtonFrame.button):
    text = "Robot Lights"
    endpoint = ":31950/robot/lights"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(_ot_2_ip, self.endpoint)
    
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


class HomeButton(metaclass=RobotButtonFrame.button):
    text = "Home"
    endpoint = ":31950/robot/home"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(_ot_2_ip, self.endpoint)
    
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


class JupyterButton(metaclass=RobotButtonFrame.button):
    text = "Jupyter"
    endpoint = ":48888"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(_ot_2_ip, self.endpoint)
    
    def command(self):
        webbrowser.open(self.url)
