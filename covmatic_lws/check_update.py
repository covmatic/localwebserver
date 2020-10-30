from . import __version__
import os
from typing import Tuple, Iterable, Callable
from itertools import zip_longest
from functools import partialmethod
import operator


class Version(str):
    sep = '.'
    
    def as_iter(self) -> Iterable[int]:
        for x in self.split(self.sep):
            try:
                yield int(x)
            except Exception:
                break
        
    def as_tuple(self) -> Tuple[int]:
        return tuple(self.as_iter())
    
    def compare(self, other: str, f: Callable) -> bool:
        for s, o in zip_longest(self.as_iter(), type(self)(other).as_iter(), fillvalue=0):
            if s != o:
                return f(s, o)
        return f(s, o)


for op in (
    "__lt__",
    "__le__",
    "__eq__",
    "__ne__",
    "__ge__",
    "__gt__",
):
    setattr(Version, op, partialmethod(Version.compare, f=getattr(operator, op)))


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
    return Version(lv) <= current_version, current_version, lv, cmd
