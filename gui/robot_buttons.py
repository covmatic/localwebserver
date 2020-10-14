from .button_frames import ButtonFrameBase
from .buttons import ColorChangingButton
from . import _ot_2_ip
import requests
import json


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
