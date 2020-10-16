from .args import Args
from PIL import ImageTk, Image
import requests
import os


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
    return get_pic(Args().icon_url, Args().icon_file, resize)


def get_logo(resize: float = 1):
    return get_pic(Args().logo_url, Args().logo_file, resize)


def set_ico(parent):
    parent.tk.call('wm', 'iconphoto', parent._w, get_icon())
