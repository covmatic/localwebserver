import tkinter as tk
import tkinter.messagebox
from functools import wraps
from PIL import ImageTk, Image
import requests
import os


_ot_2_ip: str = os.environ.get("OT2IP", "")
_icon_file: str = os.environ.get("ICON_FILE", "./Covmatic_Icon.jpg")
_icon_url: str = os.environ.get("ICON_URL", "https://covmatic.org/wp-content/uploads/2020/10/cropped-Favicon-180x180.jpg")
_logo_file: str = os.environ.get("LOGO_FILE", "./Covmatic_Logo.png")
_logo_url: str = os.environ.get("LOGO_URL", "https://covmatic.org/wp-content/uploads/2020/06/logo-1.png")
_opentrons_app: str = os.environ.get("OPENTRONS_APP", "C:/Program Files/Opentrons/Opentrons.exe")
_web_app: str = os.environ.get("WEB_APP_URL", "https://ec2-15-161-32-20.eu-south-1.compute.amazonaws.com/stations")
_station: str = os.environ.get("STATION_NAME", "A")
_remote_protocol_file: str = os.environ.get("PROTOCOL_REMOTE", "/var/lib/jupyter/notebooks/protocol.py")
_local_protocol_file: str = os.environ.get("PROTOCOL_LOCAL", "./.protocol.py")
_message_lang: str = os.environ.get("PROTOCOL_LANG", "ENG")
_kill_app: bool = True


def get_pic(url: str, file: str, resize: float = 1):
    if not os.path.exists(file):
        response = requests.get(url)
        with open(file, 'wb') as f:
            f.write(response.content)
    if os.path.exists(file) and os.path.isfile(file):
        img = Image.open(file)
        if resize != 1:
            img = img.resize([int(resize * d) for d in img.size])
        return ImageTk.PhotoImage(image=img)


def get_icon(resize: float = 1):
    return get_pic(_icon_url, _icon_file, resize)


def get_logo(resize: float = 1):
    return get_pic(_logo_url, _logo_file, resize)


def set_ico(parent):
    parent.tk.call('wm', 'iconphoto', parent._w, get_icon())


def warningbox(foo):
    @wraps(foo)
    def foo_(*args, **kwargs):
        try:
            return foo(*args, **kwargs)
        except Exception as e:
            tk.messagebox.showwarning(type(e).__name__, str(e))
    return foo_
