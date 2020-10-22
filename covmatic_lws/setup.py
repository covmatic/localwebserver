from .utils import FunctionCase
import os


setup = FunctionCase(os.sys.platform)


@setup.case('linux')
def linux_setup(
    script: str,
    desktop_file: str = os.path.expanduser("~/.local/share/applications/covmatic.desktop"),
    python: str = os.sys.executable
):
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    with open(desktop_file, "w") as df:
        with open(os.path.join(template_dir, "covmatic.desktop"), "r") as tf:
            df.write(tf.read().format(python, os.path.join(template_dir, "Covmatic_Icon.ico")))


if __name__ == "__main__":
    setup(*os.sys.argv)
