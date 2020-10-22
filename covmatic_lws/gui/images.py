from ..args import Args
from PIL import ImageTk, Image
import requests
import os


def get_pic(url: str, file: str, resize: float = 1):
    if not os.path.exists(file):
        response = requests.get(url)
        os.makedirs(os.path.dirname(file), exist_ok=True)
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


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
