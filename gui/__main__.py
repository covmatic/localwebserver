"""Launch the GUI for the local machine."""
from .args import Args


Args.parse(__doc__)


from .utils import try_ssh


if not try_ssh():
    raise RuntimeError("Cannot connect to {}".format(Args().ip))


from .gui import Covmatic
from .images import set_ico
import tkinter as tk
import os


root = tk.Tk()
root.title('Covmatic GUI')
set_ico(root)

covmatic = Covmatic(root)
covmatic.grid()

root.mainloop()
os.kill(os.getpid(), 9)
