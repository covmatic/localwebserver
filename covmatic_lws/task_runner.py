from __future__ import annotations
from .ssh import SSHClient
from .args import Args
from .utils import locked, classproperty
import subprocess
import threading
import logging
from typing import Optional
from abc import ABCMeta, abstractmethod


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


class StationTask(Task):
    class StationTaskThread(threading.Thread):
        def __init__(self, task: Task, *args, **kwargs):
            super(StationTask.StationTaskThread, self).__init__(*args, **kwargs)
            self.task = task
        
        def run(self):
            logging.getLogger().info("Starting protocol: {}".format(self.task))
            with SSHClient() as client:
                channel = client.invoke_shell()
                channel.send('opentrons_execute {} -n \n'.format(Args().protocol_remote))
                channel.send('exit \n')
                code = channel.recv_exit_status()
            logging.getLogger().info("Protocol exit code: {}".format(code))
    
    def new_thread(self) -> threading.Thread:
        return StationTask.StationTaskThread(self)


class PCRTask(Task):
    def new_thread(self) -> threading.Thread:
        return threading.Thread(target=subprocess.call, args=(Args().pcr_app,))


TaskDefinition(1, "stationA", StationTask)
TaskDefinition(2, "stationB", StationTask)
TaskDefinition(3, "stationC", StationTask)
TaskDefinition(4, "PCR", PCRTask)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.