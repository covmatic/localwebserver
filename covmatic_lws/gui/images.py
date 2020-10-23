import tkinter as tk
from _tkinter import TclError
from PIL import ImageTk, Image
import os
from functools import partial


_image_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


def get_pic(filename: str, filedir: str = _image_dir, resize: float = 1):
    img = Image.open(os.path.join(filedir, filename))
    if resize != 1:
        img = img.resize([int(resize * d) for d in img.size])
    return ImageTk.PhotoImage(image=img)


def get_icon(fname="Covmatic_Icon.png", resize: float = 1):
    return get_pic(fname, resize=resize)


def get_logo(resize: float = 1):
    return get_pic("Covmatic_Logo.png", resize=resize)


def set_ico(parent, icon_file_prefix: str = "Covmatic_Icon"):
    fname = partial("{}.{}".format, icon_file_prefix)
    try:
        parent.iconphoto(True, tk.PhotoImage(file=os.path.join(_image_dir, fname("ico"))))
    except TclError:
        parent.tk.call('wm', 'iconphoto', parent._w, get_icon(fname("png")))


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
