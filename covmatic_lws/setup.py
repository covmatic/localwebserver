from .args import Args
from .utils import FunctionCaseStartWith
import logging
import os


setup = FunctionCaseStartWith(os.sys.platform)


@setup.case('linux')
def linux_setup():
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    if Args().desktop_file:
        with open(Args().desktop_file, "w") as df:
            with open(os.path.join(template_dir, "covmatic.desktop"), "r") as tf:
                df.write(tf.read().format(Args().python, os.path.join(template_dir, "Covmatic_Icon.ico")))
    else:
        logging.getLogger().warning("No desktop file specified, skipping")
    if Args().tempdeck_desktop:
        if Args().tempdeck_desktop_file:
            with open(Args().tempdeck_desktop_file, "w") as df:
                with open(os.path.join(template_dir, "covmatic_tempdeck.desktop"), "r") as tf:
                    df.write(tf.read().format(Args().python, os.path.join(template_dir, "Covmatic_Icon_Red.ico")))
        else:
            logging.getLogger().warning("No tempdeck desktop file specified, skipping")


@setup.case(('win32', 'cygwin'))
def win_setup():
    import winshell
    import win32con
    winshell.Shortcut.show_states["min"] = win32con.SW_SHOWMINNOACTIVE
    
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    if Args().desktop_file:
        with winshell.shortcut(Args().desktop_file) as link:
            link.path = os.sys.executable
            link.arguments = "-m covmatic_lws.gui"
            link.description = "Covmatic LocalWebServer GUI"
            link.show_cmd = "min"
            link.icon_location = (os.path.join(template_dir, "Covmatic_Icon.ico"), 0)
    else:
        logging.getLogger().warning("No desktop file specified, skipping")
    if Args().tempdeck_desktop:
        if Args().tempdeck_desktop_file:
            with winshell.shortcut(Args().tempdeck_desktop_file) as link:
                link.path = os.sys.executable
                link.arguments = "-m covmatic_lws.gui.tempdeck"
                link.description = "Covmatic TempDeck GUI"
                link.show_cmd = "min"
                link.icon_location = (os.path.join(template_dir, "Covmatic_Icon_Red.ico"), 0)
        else:
            logging.getLogger().warning("No tempdeck desktop file specified, skipping")
            

@setup.case('')
def other_setup():
    logging.getLogger().warning("No setup action defined for platform {}".format(os.sys.platform))
    

if __name__ == "__main__":
    setup()
