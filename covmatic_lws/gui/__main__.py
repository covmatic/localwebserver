"""Launch the GUI for the local machine."""
import tkinter as tk
import tkinter.messagebox
import os
from ..check_update import up_to_date


up2date, cv, lv, up_cmd = up_to_date()
if not up2date:
    root = tk.Tk()
    root.title("Covmatic GUI")
    root.withdraw()
    update = tk.messagebox.askyesno(
        "Update avaliable",
        "You are using the Covmatic LocalWebserver version {},\nbut version {} is available.\n\nDo you want to upgrade?".format(cv, lv),
        parent=root,
    )
    if update:
        os.system("{} && {} -m covmatic_lws.gui".format(up_cmd, os.sys.executable))
    root.destroy()
    if update:
        exit()


from .gui import Covmatic
from .images import set_ico
import tkinter as tk


root = tk.Tk()
root.title('Covmatic GUI')
set_ico(root)

covmatic = Covmatic(root)
covmatic.grid()

root.mainloop()
os.kill(os.getpid(), 9)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
