from .args import Args
import paramiko as pk
from scp import SCPClient
import socket
from .utils import locked
from threading import Lock


class SSHClient(pk.SSHClient):
    class SCPClientContext(SCPClient):
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()
            return exc_val is None
        
    def __init__(self, usr: str = Args().user, ip_addr: str = Args().ip, key_file: str = Args().ssh_key, pwd: str = Args().pwd, connect_kwargs: dict = {}):
        super(SSHClient, self).__init__()
        self._usr = usr
        self._ip_addr = ip_addr
        self._key_file = key_file
        self._pwd = pwd
        self.set_missing_host_key_policy(pk.AutoAddPolicy())  # It is needed to add the device policy
        self._connect_kwargs = connect_kwargs
    
    def __enter__(self):
        self.connect(self._ip_addr, username=self._usr, key_filename=self._key_file, password=self._pwd, **self._connect_kwargs)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):  
        self.close()
        return exc_val is None
    
    def scp_client(self) -> SCPClientContext:
        return self.SCPClientContext(self.get_transport())


_try_ssh_cache = None
_try_ssh_lock = Lock()


@locked(_try_ssh_lock)
def try_ssh(timeout: float = 0.5, force: bool = False) -> bool:
    global _try_ssh_cache
    if _try_ssh_cache is None or force:
        try:
            with SSHClient(connect_kwargs=dict(timeout=timeout)):
                _try_ssh_cache = True
        except Exception:
            _try_ssh_cache = False
    return _try_ssh_cache


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
