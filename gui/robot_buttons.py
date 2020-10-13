from .button_frames import ButtonFrameBase
from .buttons import ColorChangingButton
from . import _ot_2_ip
import requests


class RobotButtonFrame(ButtonFrameBase):
    pass


class LightsButton(ColorChangingButton, metaclass=RobotButtonFrame.button):
    text = "Robot Lights"
    endpoint = ":31950/robot/lights"
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(_ot_2_ip, self.endpoint)
    
    @property
    def state(self) -> bool:
        try:
            state = requests.get(self.url).json().get("on", False)
        except requests.exceptions.ConnectionError:
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
