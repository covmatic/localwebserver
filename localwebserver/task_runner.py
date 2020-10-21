from .ssh import SSHClient
from .args import Args
from .api import ActionFunction
from .utils import loop
import subprocess
import logging


def print_info():
    logging.getLogger().info("Target Opentrons IP: {}".format(Args().ip))


def station_task(station, action):
    with SSHClient() as client:
        channel = client.invoke_shell()
        channel.send('opentrons_execute {} -n \n'.format(Args().protocol_remote))
        channel.send('exit \n')
        code = channel.recv_exit_status()
    logging.getLogger().info("Protocol exit code: {}".format(code))


def pcr_task(station, action):
    subprocess.call(Args().pcr_app)


_tasks = [
    (1, "stationA", station_task),
    (2, "stationB", station_task),
    (3, "stationC", station_task),
    (4, "PCR", pcr_task),
]


@loop(5)
def check_new_tasks():
    if ActionFunction.station and ActionFunction.action:
        for s, a, foo in _tasks:
            if ActionFunction.station == s and ActionFunction.action == a:
                logging.getLogger().info("Protocol: station={}, action={}".format(s, a))
                foo(s, a)
                ActionFunction.station = None
                ActionFunction.action = None
                return
        logging.getLogger().info("Unsupported protocol: station={}, action={}".format(s, a))


def start():
    print_info()
    check_new_tasks.start()


def stop():
    check_new_tasks.stop()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
