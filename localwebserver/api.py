"""LocalWebServer API"""
from database import session
import requests
from flask_restful import Resource
from flask_restful import reqparse
from models.protocols import Protocol
import glob
import os
from shutil import copy2
import json
from .args import Args
import threading
from .utils import SingletonMeta, locked
from .ssh import try_ssh, SSHClient
from flask_restful import Api
import logging


class LocalWebServerAPI(Api):
    def __init__(self, prefix=Args().api_prefix, *args, **kwargs):
        super(LocalWebServerAPI, self).__init__(*args, prefix=prefix, **kwargs)
        self.add_resource(CheckFunction, '/check')
        self.add_resource(PauseFunction, '/pause')
        self.add_resource(ResumeFunction, '/resume')


class BarcodeSingleton(str, metaclass=SingletonMeta):
    lock = threading.Lock()


class CheckFunction(Resource):
    bak_lock = threading.Lock()
    _bak = {}
    _running = False
    
    @property
    def logger(self) -> logging.getLoggerClass():
        return logging.getLogger(type(self).__name__)
    
    @property
    @locked(bak_lock)
    def protocol_running(self) -> bool:
        # If a temporary error occurs, respond same as before
        if try_ssh():
            with SSHClient() as client:
                # TODO: update this when refactored as a service
                _, stdout, _ = client.exec_command("ps -e | grep opentrons_execute | grep -v grep")
                CheckFunction._running = bool(stdout.read().decode('ascii'))
        return CheckFunction._running
    
    @classmethod
    @locked(bak_lock)
    def bak(cls, value=None, force: bool = False):
        if value is not None or force:
            cls._bak = value
        return cls._bak
    
    def get(self):
        if self.protocol_running:
            with BarcodeSingleton.lock:
                try:
                    rv = requests.get("http://{}:8080/log".format(Args().ip))
                except requests.exceptions.ConnectionError:
                    self.logger.info("{} - Connection Error".format("http://{}:8080/log".format(Args().ip)))
                else:
                    self.logger.info("{} - Status Code {}".format(self.log_endpoint, rv.status_code))
                    self.logger.debug(rv.content.decode('ascii'))
                    if rv.status_code == 200:
                        CheckFunction.bak(rv.json())
                finally:
                    output = CheckFunction.bak()
                if output.get("external", False):
                    while not BarcodeSingleton():
                        BarcodeSingleton.reset(requests.get("http://127.0.0.1:{}/exit".format(Args().barcode_port)).content.decode('ascii'))
            return {
                       "status": False,
                       "res": "Status: {}\nStage: {}{}".format(
                           output.get("status", None),
                           output.get("stage", None),
                           "\n\n{}".format(output["msg"]) if output.get("msg", None) else ""
                       )
                   }, 200
        else:
            with CheckFunction.bak_lock:
                if CheckFunction.bak() is None:
                    # No protocol is running, look for PCR result files
                    pcr_result_files = glob.glob(Args().pcr_results).sort(key=os.path.getctime)
                    if pcr_result_files:
                        try:
                            with open(str(pcr_result_files[-1]), 'r', encoding='utf-8-sig') as f:
                                result = json.load(f)
                        except Exception as e:
                            return {"status": True, "res": str(e)}, 500
                        # Make a backup of the PCR results
                        os.makedirs(Args().pcr_backup, exist_ok=True)
                        copy2(pcr_result_files[-1], Args().pcr_backup)
                        # Delete the last file in order to not create confusion
                        os.remove(pcr_result_files[-1])
                        return {"status": True, "res": result}, 200
                    else:
                        return {"status": True, "res": "No Protocol nor Result available"}, 200
                else:
                    # Protocol has ended, reset backup
                    CheckFunction.bak(force=True)
                    self.logger.info("Protocol completed")
                    return {"status": True, "res": "Completed"}, 200


class PauseFunction(Resource):
    def get(self):
        requests.get("http://{}:8080/pause".format(Args().ip))
        return {"status": False, "res": "Pausa"}, 200


class ResumeFunction(Resource):
    @staticmethod
    def _resume():
        return requests.get("http://{}:8080/resume".format(Args().ip))
    
    @locked(BarcodeSingleton.lock)
    def get(self):
        if BarcodeSingleton():
            while requests.get("http://127.0.0.1:{}/enter".format(Args().barcode_port)).content.decode('ascii') != BarcodeSingleton():
                pass
            self._resume()
            t = threading.Timer(1, BarcodeSingleton.reset)
            t.start()
            t.join()
        else:
            self._resume()
        return {"status": False, "res": "Resumed"}, 200
        

# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
