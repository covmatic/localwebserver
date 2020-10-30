from . import __version__
from typing import Tuple
import os


def latest_version(pkg_name: str = "covmatic-localwebserver", index=None, python: str = os.sys.executable) -> str:
    for s in os.popen("{} -m pip search{} -V {}".format(
        python,
        " -i {}".format(index) if index else "",
        pkg_name)
    ).read().split("\n"):
        if s[:len(pkg_name)] == pkg_name:
            return s.split("(")[1].split(")")[0]
    return __version__


def up_to_date(current_version: str = __version__, pkg_name: str = "covmatic-localwebserver", index=None, python_lookup: str = os.sys.executable, python_install: str = None) -> Tuple[bool, str, str, str]:
    """Returns:
        up_to_date: whether the package is up to date or not
        current_version: the current version
        latest_version: the latest version on PyPI
        update_command: the command to update the package
    """
    if python_install is None:
        python_install = python_lookup
    lv = latest_version(pkg_name=pkg_name, index=index and os.path.dirname(index), python=python_lookup)
    cmd = "{} -m pip install{} --upgrade {}".format(python_install, " -i {}".format(index) if index else "", pkg_name)
    return lv == current_version, current_version, lv, cmd
