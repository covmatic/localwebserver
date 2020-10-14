import tkinter as tk
import tkinter.messagebox
from functools import wraps
from PIL import ImageTk, Image
import requests
import os


_ot_2_ip: str = os.environ.get("OT2IP", "")
_icon_file: str = os.environ.get("ICON_FILE", "./Covmatic_Icon.jpg")
_icon_url: str = os.environ.get("ICON_URL", "https://covmatic.org/wp-content/uploads/2020/10/cropped-Favicon-180x180.jpg")
_opentrons_app: str = os.environ.get("OPENTRONS_APP", "C:/Program Files/Opentrons/Opentrons.exe")
_web_app: str = os.environ.get("WEB_APP_URL", "https://ec2-15-161-32-20.eu-south-1.compute.amazonaws.com/stations")
_station: str = os.environ.get("STATION_NAME", "A")
_remote_protocol_file: str = os.environ.get("PROTOCOL_REMOTE", "/var/lib/jupyter/notebooks/protocol.py")
_local_protocol_file: str = os.environ.get("PROTOCOL_LOCAL", "./.protocol.py")
_message_lang: str = os.environ.get("PROTOCOL_LANG", "ENG")
_kill_app: bool = True


def set_ico(parent, url: str = _icon_url, file: str = _icon_file):
    if not os.path.exists(file):
        response = requests.get(url)
        with open(file, 'wb') as f:
            f.write(response.content)
    if os.path.exists(file) and os.path.isfile(file):
        icon = ImageTk.PhotoImage(Image.open(file))
        parent.tk.call('wm', 'iconphoto', parent._w, icon)


def warningbox(foo):
    @wraps(foo)
    def foo_(*args, **kwargs):
        try:
            return foo(*args, **kwargs)
        except Exception as e:
            tk.messagebox.showwarning(type(e).__name__, str(e))
    return foo_
