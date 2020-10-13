from .button_frames import ButtonFrameBase
from .buttons import OnOffSubprocessButton, SubprocessButton
from . import _web_app, _opentrons_app
import os
import webbrowser
from typing import Tuple, List


class AppButtonFrame(ButtonFrameBase):
    pass


class OpentronsButton(SubprocessButton, metaclass=AppButtonFrame.button):
    text: str = "Opentrons APP"
    endpoint = ":5001/api/check"
    
    @property
    def url(self) -> str:
        return "http://127.0.0.1{}".format(self.endpoint)
    
    def __init__(self, parent, app_file: str = _opentrons_app, *args, **kwargs):
        self._app_file = app_file 
    
    def check_app(self) -> bool:
        return os.path.exists(self._app_file) and os.path.isfile(self._app_file)
    
    _already_running: str = "Opentrons APP running", "Another instance of the Opentrons APP has already been launched"
    
    @property
    def _check_fail(self) -> Tuple[str, str]:
        return "Opentrons APP not found", "Opentrons APP not found at {}\nPlease set the correct path in the environment variable:\n\nOPENTRONS_APP".format(self._app_file)
    
    @property
    def _subprocess_args(self) -> List[str]:
        return [self._app_file]


class ServerButton(OnOffSubprocessButton, metaclass=AppButtonFrame.button):
    text: str = "Local Web Server"
    
    def __init__(self, parent, python_exe: str = os.sys.executable, python_script: str = "./app.py", *args, **kwargs):
        self._python = python_exe
        self._script = python_script
    
    def check_app(self) -> bool:
        return os.path.exists(self._python) and os.path.isfile(self._python) and os.path.exists(self._script) and os.path.isfile(self._script)
    
    _already_running: str = "LocalWebServer running", "Another instance of the LocalWebServer has already been launched"\
    
    @property
    def _check_fail(self) -> Tuple[str, str]:
        return "LocalWebServer not found", "LocalWebServer files not found (one or more):\n\n{}\n{}".format(self._python, self._script)\
    
    @property
    def _subprocess_args(self) -> List[str]:
        return [self._python, self._script]
        

class StartRunButton(metaclass=AppButtonFrame.button):
    text: str = "Start a New Run"
    
    def command(self, app_url: str = _web_app):
        webbrowser.open(app_url)
