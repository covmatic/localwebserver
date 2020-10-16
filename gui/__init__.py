import tkinter as tk
import tkinter.messagebox
from functools import wraps
from PIL import ImageTk, Image
from services.task_runner import SSHClient
import socket
import requests
import json
import os


_env_defaults = {} 
with open(os.path.join(os.path.dirname(__file__), "env_defaults.json"), "r") as f:
    _env_defaults = json.load(f)


def environ_get(key: str):
    return os.environ.get(key, _env_defaults.get(key, None))


_ot_2_ip: str = environ_get("OT2IP")
_icon_file: str = environ_get("ICON_FILE")
_icon_url: str = environ_get("ICON_URL")
_logo_file: str = environ_get("LOGO_FILE")
_logo_url: str = environ_get("LOGO_URL")
_opentrons_app: str = environ_get("OPENTRONS_APP")
_web_app: str = environ_get("WEB_APP_URL")
_station: str = environ_get("STATION_NAME")
_remote_protocol_file: str = environ_get("PROTOCOL_REMOTE")
_local_protocol_file: str = environ_get("PROTOCOL_LOCAL")
_message_lang: str = environ_get("PROTOCOL_LANG")
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


def try_ssh(timeout: float = 1) -> bool:
    try:
        with SSHClient(connect_kwargs=dict(timeout=timeout)):
            return True
    except socket.timeout:
        return False


if not _ot_2_ip:
    raise ValueError("Robot IP address not set.\nPlease set the environment variable:\nOT2IP")
if not try_ssh():
    raise TimeoutError("Cannot connect to {}".format(_ot_2_ip))
