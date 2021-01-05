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
from requests.auth import HTTPDigestAuth
import glob
import socket
import queue


task_fwd_queue = queue.Queue()
task_bwd_queue = queue.Queue()


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
                    logging.getLogger().info("Copied '{}' to '{}'".format(self._local, self._remote))
                # Set environment key
                ssh_channel.send('export {}=\"{}\"\n'.format(self._env_key, self._remote))
                logging.getLogger().info('Using {}=\"{}\"'.format(self._env_key, self._remote))

    magnet_config = StationConfigFile(Args().magnet_json_local, Args().magnet_json_remote, "OT_MAGNET_JSON")
    copan48_config = StationConfigFile(Args().copan48_json_local, Args().copan48_json_remote, "OT_COPAN_48_CORRECT")

    class StationTaskThread(threading.Thread):
        def __init__(self, task: Task, *args, **kwargs):
            super(StationTask.StationTaskThread, self).__init__(*args, **kwargs)
            self.task = task

        def run(self):
            logging.getLogger().info("Starting protocol: {}".format(self.task))
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
                        channel.recv(1024)
                    except Exception:
                        pass
                    channel.settimeout(None)
                code = channel.recv_exit_status()
            with Task.lock:
                Task.exit_code = code
            logging.getLogger().info("Protocol exit code: {}".format(code))

    def new_thread(self) -> threading.Thread:
        return StationTask.StationTaskThread(self)


@task_definition(4, "PCR")
class PCRTask(Task):

    def new_thread(self) -> threading.Thread:
        # Clean the results of the PCR before starting the process
        pcr_result_files = glob.glob(Args().pcr_results)
        if pcr_result_files:
            for f in pcr_result_files:
                logging.debug('file removed: {}'.format(f))
                os.remove(f)
        else:
            logging.debug('PCR results folder already clean!')
        return threading.Thread(target=subprocess.call, args=(Args().pcr_app,))


@task_definition(0, "YuMistart")
class YumiTaskStart(Task):
    class YumiTaskStartThread(threading.Thread):
        def __init__(self):
            super().__init__()
            # Controller IP
            # TODO: CHECK IF THE HOSTNAME IS THIS OR IF I HAVE TO USE THE LOCALHOST
            self.hostname = 'http://192.168.125.1'
            self.start_url = '/rw/rapid/execution?action=start'
            # Parameters for starting all the tasks of the Yumi
            # TODO: CHECK THE PAYLOAD
            self.start_payload = {'regain': 'continue', 'execmode': 'continue', 'cycle': 'once',
                                  'condition': 'none', 'stopatbp': 'disabled', 'alltaskbytsp': 'true'}

        def run(self):
            try:
                start = requests.post(self.hostname + self.start_url,
                                      auth=HTTPDigestAuth("Default User", "robotics"),
                                      data=self.start_payload)
                if start.status_code == 400:
                    # It should answers the controller with the error if any
                    logging.warning("Execution error {}".format(start.json()))
                    # Only connection error -> Probably this will merge in a >= condition.
                elif start.status_code > 400:
                    logging.warning("Connection error, Status code: {}".format(start.status_code))
                logging.info("Status code: {} \n Controller response {}".format(start.status_code, start.json()))
            except requests.exceptions.ConnectionError as err:
                logging.warning("Connection error {}".format(err))

    def new_thread(self) -> threading.Thread:
        return YumiTaskStart.YumiTaskStartThread()


@task_definition(0, "YuMi")
class YumiTask(Task):
    class YumiTaskThread(threading.Thread):
        def __init__(self, port: int = 1025):
            super().__init__()
            # Using raw sockets because of Rapid API
            self.port = port

        def run(self):
            server = socket.create_server(("", self.port))
            conn_sock, cli_addr = server.accept()
            logging.info("Established connection with %s", cli_addr)
            while True:
                req = conn_sock.recv(4096)
                if not req:
                    logging.info("Connection with %s interrupted. Closing task", cli_addr)
                    break
                # FIXME: Comparing strings of natural language text as a way of decoding message types is really bad practise. Remember how it broke the number of samples in the PWA
                if req.decode() == 'Non ho ricevuto nulla...':
                    logging.warning("Barcode has not been scanned")
                else:
                    barcode = req.decode()
                    logging.info("Received barcode: %s", barcode)
                    # Enqueue barcode for forwarding (must be a valid JSON string)
                    # Converted into a string
                    task_fwd_queue.put('{}'.format(barcode))
                    # Next call to chek will return all newly enqueued barcodes
                    # TODO: Ricevere OK DA LIS/TRACCIABILITÀ se il barcode è conforme
                    # VARIABILE STATICA PER SIMULAZIONE CON YUMI
                    # OK = "OK"
                    # Aspetta finché un elemento non è disponibile
                    OK = task_bwd_queue.get()
                    if OK == "OK":
                        logging.info('Compliant barcode: {}'.format(barcode))
                    else:
                        logging.warning('Non-compliant barcode: {}'.format(barcode))
                    # Manda OK/NONOK allo YuMi per decidere se scartare la provetta o meno
                    conn_sock.sendall(OK.encode())

    # TODO: Create a task that execute a Python module which returns the position
    # of the barcode and the barcode
    def new_thread(self) -> threading.Thread:
        return YumiTask.YumiTaskThread()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
