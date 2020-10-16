from .args import Args
import tkinter as tk
import tkinter.messagebox
from functools import wraps
import socket
from services import task_runner


def SSHClient(
    ip_addr: str = Args().ip,
    key_file: str = Args().ssh_key,
    pwd: str = Args().pwd,
    **kwargs
) -> task_runner.SSHClient:
    return task_runner.SSHClient(
        ip_addr=ip_addr,
        key_file=key_file,
        pwd=pwd,
        **kwargs
    )


def warningbox(foo):
    @wraps(foo)
    def foo_(*args, **kwargs):
        try:
            return foo(*args, **kwargs)
        except Exception as e:
            tk.messagebox.showwarning(type(e).__name__, str(e))
    return foo_


def try_ssh(timeout: float = 1) -> bool:
    try:
        with SSHClient(connect_kwargs=dict(timeout=timeout)):
            return True
    except (socket.timeout, socket.gaierror):
        return False
