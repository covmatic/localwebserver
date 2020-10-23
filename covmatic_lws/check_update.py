from . import __version__
from typing import Tuple
import os


def latest_version() -> str:
    pkg_name = "covmatic-localwebserver"
    for s in os.popen("{} -m pip search{} -V {}".format(
        os.sys.executable,
        " -i https://test.pypi.org/pypi/",
        pkg_name)
    ).read().split("\n"):
        if s[:len(pkg_name)] == pkg_name:
            return s.split("(")[1].split(")")[0]
    return __version__


def up_to_date() -> Tuple[bool, str, str]:
    """Returns:
        up_to_date: wheter the package is up to date or not
        current_version: the current version
        latest_version: the latest version on PyPI
    """
    lv = latest_version()
    return lv == __version__, __version__, lv
