from __future__ import annotations
from .ssh import SSHClient
from .args import Args
from .utils import locked, classproperty
import subprocess
import threading
import logging
from typing import Optional
from abc import ABCMeta, abstractmethod
import os
import requests
import glob
import socket
import queue
import time


task_fwd_queue = queue.Queue()
task_bwd_queue = queue.Queue()
task_finished_queue = queue.Queue()

logger = logging.getLogger(__name__)


class TaskDefinition:
    _list = []

    @classmethod
    def get(cls, station, action):
        for t in cls._list:
            if t.station == station and t.action == action:
                return t
        raise KeyError("Cannot find a {} for keys: station={}, action={}".format(cls.__name__, station, action))

    def __init__(self, station, action, cls, *args, **kwargs):
        TaskDefinition._list.append(self)
        self.station = station
        self.action = action
        self.cls = cls
        self.args = args
        self.kwargs = kwargs


def task_definition(station, action, *args, **kwargs):
    def td_(cls):
        td = TaskDefinition(
            station,
            action,
            cls,
            *args,
            **kwargs
        )
        return cls
    return td_


class TaskMeta(ABCMeta):
    def __call__(cls, station, action):
        td = TaskDefinition.get(station, action)
        self = td.cls.__new__(td.cls, *td.args, station=td.station, action=td.action, **td.kwargs)
        self.__init__(*td.args, station=td.station, action=td.action, **td.kwargs)
        return self


class Task(metaclass=TaskMeta):
    class TaskRunningException(Exception):
        pass

    lock = threading.Lock()
    _running: Optional[Task] = None
    exit_code: int = None

    def __init__(self, station, action, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        self.station = station
        self.action = action
        self._thread = None

    @classproperty
    def running(self) -> bool:
        if Task._running is None or Task._running._thread is None:
            return False
        if not Task._running._thread.is_alive():
            Task._running._thread.join()
            Task._running._thread = None
            Task._running = None
            return False
        return True

    @classproperty
    def type(self) -> type:
        return type(Task._running)

    @abstractmethod
    def new_thread(self) -> threading.Thread:
        pass

    @locked(lock)
    def start(self):
        if Task.running:
            raise Task.TaskRunningException("Cannot start {}: a {} is already running".format(self, Task._running))
        Task._running = self
        self._thread = self.new_thread()
        Task._running._thread.start()

    _str_fields = ("station", "action")

    def __str__(self) -> str:
        return "{} ({})".format(type(self).__name__, ", ".join("{}={}".format(k, getattr(self, k)) for k in self._str_fields))


class SshBufferPrinter(object):
    def __init__(self, logger):
        self.logger = logger
        self.buffer = ""

    def append_and_printline(self, new_byte_string):
        self.buffer += new_byte_string.decode('utf-8')
        if "\n" in self.buffer:
            self.flush_and_printline()

    def flush_and_printline(self):
        for l in self.buffer.splitlines():
            self.logger(l)
        self.buffer = ""

@task_definition(1, "stationA")
@task_definition(2, "stationB")
@task_definition(3, "stationC")

class StationTask(Task):
    class StationConfigFile:
        def __init__(self, local, remote, env_key: str):
            self._local = local
            self._remote = remote
            self._env_key = env_key

        def push(self, ssh_client: SSHClient, ssh_channel):
            if self._remote:
                # Copy over configuration
                if os.path.isfile(self._local):
                    ssh_client.exec_command("mkdir -p {}".format(os.path.dirname(self._remote)))
                    with ssh_client.scp_client() as scp_client:
                        scp_client.put(self._local, self._remote)
                    logger.info("Copied '{}' to '{}'".format(self._local, self._remote))
                # Set environment key
                ssh_channel.send('export {}=\"{}\"\n'.format(self._env_key, self._remote))
                logger.info('Using {}=\"{}\"'.format(self._env_key, self._remote))

    magnet_config = StationConfigFile(Args().magnet_json_local, Args().magnet_json_remote, "OT_MAGNET_JSON")
    copan48_config = StationConfigFile(Args().copan48_json_local, Args().copan48_json_remote, "OT_COPAN_48_CORRECT")

    class StationTaskThread(threading.Thread):
        def __init__(self, task: Task, *args, **kwargs):
            super(StationTask.StationTaskThread, self).__init__(*args, **kwargs)
            self.task = task
            self.info_printer = SshBufferPrinter(logging.getLogger("SSH").info)
            self.err_printer = SshBufferPrinter(logging.getLogger("SSH").error)

        def run(self):
            logger.info("Starting protocol: {}".format(self.task))
            # Try to reset the run log
            try:
                requests.get("http://127.0.0.1:{}/reset_log".format(Args().barcode_port))
            except Exception:
                pass
            with Task.lock:
                Task.exit_code = -1
            with SSHClient() as client:
                channel = client.invoke_shell()
                # Copy over configurations
                StationTask.magnet_config.push(client, channel)
                StationTask.copan48_config.push(client, channel)
                # Launch protocol
                channel.send('opentrons_execute {} -n \n'.format(Args().protocol_remote))
                # Wait for exit code
                channel.send('exit \n')

                while not channel.exit_status_ready():
                    channel.settimeout(1)
                    try:
                        self.info_printer.append_and_printline(channel.recv(1024))
                        if channel.recv_stderr_ready():
                            self.err_printer.append_and_printline(channel.recv_stderr(1024))
                    except Exception:
                        pass

                    channel.settimeout(None)

                self.info_printer.flush_and_printline()
                self.err_printer.flush_and_printline()

                code = channel.recv_exit_status()
            with Task.lock:
                Task.exit_code = code
            logger.info("Protocol exit code: {}".format(code))

    def new_thread(self) -> threading.Thread:
        return StationTask.StationTaskThread(self)


@task_definition(4, "PCR")
class PCRTask(Task):

    def new_thread(self) -> threading.Thread:
        # Clean the results of the PCR before starting the process
        pcr_result_files = glob.glob(Args().pcr_results)
        if pcr_result_files:
            for f in pcr_result_files:
                logger.debug('file removed: {}'.format(f))
                os.remove(f)
        else:
            logger.debug('PCR results folder already clean!')
        return threading.Thread(target=subprocess.call, args=(Args().pcr_app,))


@task_definition(0, "YuMi")
class YumiTask(Task):
    class YumiTaskThread(threading.Thread):
        def __init__(self, port: int = 1025):
            super().__init__()
            # Using raw sockets because of Rapid API
            self.port = port
            self.socket_timeout = 20

        def run(self):
            with task_finished_queue.mutex:
                task_finished_queue.queue.clear()
            logger.info("Yumi Task started!")
            server = socket.create_server(("", self.port))
            logger.debug("Created.")
            server.settimeout(self.socket_timeout)
            conn_sock, cli_addr = server.accept()
            logger.info("Established connection with %s", cli_addr)
            logger.debug("Waiting for robot data...")
            conn_sock.settimeout(self.socket_timeout)
            try:
                # Wait until robot has a sample
                while True:
                    req = conn_sock.recv(4096)
                    logger.debug("Received from robot: {}".format(req.decode()))
                    if not req or req.decode() != "Searching":
                        break
                logger.debug("Robot data received: {}".format(req.decode()))
                if req:
                    while not task_bwd_queue.empty():
                        task_bwd_queue.get()
                    # FIXME: Comparing strings of natural language text as a way
                    #  of decoding message types is really bad practise.
                    #  Remember how it broke the number of samples in the PWA
                    if req.decode() == 'Non ho ricevuto nulla...':
                        task_fwd_queue.put(({
                            "status": True,
                            "res": "EMPTY"
                        }, 200))
                        logger.warning("Barcode has not been scanned")
                    else:
                        barcode = req.decode()
                        logger.info("Received barcode: %s", barcode)
                        # Enqueue barcode for forwarding (must be a valid JSON string)
                        # Converted into a string
                        task_fwd_queue.put(({
                            "status": True,
                            "res": "{}".format(barcode)
                        }, 200))
                        # Next call to check will return all newly enqueued barcodes
                        # VARIABILE STATICA PER SIMULAZIONE CON YUMI
                        # OK = "OK"
                        # Aspetta finché un elemento non è disponibile
                        OK = task_bwd_queue.get()
                        if OK == "OK":
                            logger.info('Compliant barcode: {}'.format(barcode))
                        else:
                            logger.warning('Non-compliant barcode: {}'.format(barcode))
                        # Manda OK/NONOK allo YuMi per decidere se scartare la provetta o meno
                        conn_sock.sendall(OK.encode())
                        logger.debug("Waiting for socketo to close...")
                else:
                    logger.info("Connection with %s interrupted.", cli_addr)
                logger.info("task shoudl close now..")
                while True:
                    req2 = conn_sock.recv(4096)
                    if not req2:
                        logger.debug("closed")
                        break
            finally:
                task_finished_queue.put("CLOSED")

    class YumiTaskThreadSimulation(YumiTaskThread):
        class Increment:
            def __init__(self):
                self.i = 0

            def getIncrement(self):
                self.i += 1
                return self.i

        increment = Increment()
        iterationsToReturnError = 2

        def __init__(self):
            self._incrementObj = self.increment
            logger.info("Yumi simulation!")
            super().__init__()

        def run(self):
            logger.info("Yumi task started!")
            time.sleep(0.5)
            i = self._incrementObj.getIncrement()
            if i == self.iterationsToReturnError:
                obj = {
                    "status": True,
                    "res": "EMPTY"
                }
                task_fwd_queue.put((obj, 200))
            else:
                logger.info("returning barcode")
                obj = {
                    "status": True,
                    "res": "helloWorld{}".format(i)
                }
                task_fwd_queue.put((obj, 200))

    # TODO: Create a task that execute a Python module which returns the position
    #  of the barcode and the barcode
    def new_thread(self) -> threading.Thread:
        return YumiTask.YumiTaskThread()
        # return YumiTask.YumiTaskThreadSimulation()     # Use this class to simulate the Yumi

# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
