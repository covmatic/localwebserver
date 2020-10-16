from database import session
# from flask import jsonify
import requests
import tkinter as tk
from flask_restful import Resource
from flask_restful import reqparse
from functools import wraps, partial, update_wrapper
from models.protocols import Protocol
from tkinter import simpledialog
# from sqlalchemy import or_, desc
import glob
import os
from shutil import copy2
import json
import time
from typing import Optional, Any
# from services.task_runner import create_ssh_client
# from scp import SCPClient
from gui.args import Args
import threading
import signal
from .utils import SingletonMeta


# from services.task_runner import OT2_SSH_KEY, OT2_ROBOT_PASSWORD, OT2_REMOTE_LOG_FILEPATH

if not Args().__dict__:
    Args.parse("API protocol automation.")


def gui_user_input(f, *args, **kwargs):
    root = tk.Tk()
    root.withdraw()
    root.call('wm', 'attributes', '.', '-topmost', True)
    root.lift()
    root.attributes('-topmost', True)
    s = f(*args, **kwargs)
    root.destroy()
    return s


class BarcodeSingleton(str, metaclass=SingletonMeta):
    pass


class CheckFlag:
    lock = threading.Lock()


def locked(lock):
    def _locked(foo):
        @wraps(foo)
        def _foo(*args, **kwargs):
            with lock:
                r = foo(*args, **kwargs)
            return r
        return _foo
    return _locked


# Define endpoint methods
# noinspection PyMethodMayBeStatic
class AutomationAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('process_uuid', type=str, help='process uuid to search for', required=False)
        args = parser.parse_args()
        process_uuid = args['process_uuid']
        runs_list = list()
        if process_uuid:
            runs = Protocol.query.filter_by(process_uuid=args['process_uuid']).all()
            for s in runs:
                runs_list.append(s.serialize())
        else:
            runs = Protocol.query.filter_by().all()
            for s in runs:
                runs_list.append(s.serialize())
        return runs_list, 200


# noinspection PyMethodMayBeStatic
class AutomationAPI_MVP(Resource):

    def get(self, station, action):
        try:
            queued_protocols = Protocol.query.filter_by(status='queued').all()
            running_protocols = Protocol.query.filter_by(status='running').all()
            if not (queued_protocols or running_protocols):
                protocol = Protocol(
                    station=station,
                    action=action
                )
                session.add(protocol)
                session.commit()
                res = {"status": protocol.status, "id": protocol.id}
                return res, 201
            else:
                res = {"status": "failed",
                       "message": "There's a task already queued or in progress. Please try again later"}
                return res, 403
        except Exception as e:
            res = {"status": "failed", "message": str(e)}
            return res, 500


# noinspection PyMethodMayBeStatic
class CheckFunction(Resource):
    bak_lock = threading.Lock()
    _bak = {}
    
    @classmethod
    @locked(bak_lock)
    def bak(cls, value=None):
        if value is not None:
            cls._bak = value
        return cls._bak
    
    def get(self):
        queued_protocols = Protocol.query.filter_by(status='queued').all()
        running_protocols = Protocol.query.filter_by(status='running').all()
        protocol1 = Protocol.query.filter_by(status="running").first()
        if not (queued_protocols or running_protocols):
            # FIXME: Check this
            last_protocol = Protocol.query.order_by(Protocol.creation_date.desc()).first()
            last_status = last_protocol.status
            print(last_status)
            if last_status == "failed":
                # last_protocol.set_running()
                session.remove()
                # session.add(last_protocol)
                session.commit()
                return "There has been an error in execution, please verify and try again", 400
            else:
                # Searching all PCR results file
                PCR_result_file = glob.glob(Args().pcr_results)
                # Sorting the PCR's results
                PCR_result_file.sort(key=os.path.getctime)
                # Check if the results are available
                if not PCR_result_file:
                    print('there are no results available')
                    return {"status": True, "res": ":)"}, 200
                else:
                    # Opening the the last created and encoded with utf-8-sig
                    with open(str(PCR_result_file[-1]), 'r', encoding='utf-8-sig') as result:
                        read = json.load(result)
                    # Make the backup of the PCR results
                    copy2(PCR_result_file[-1], './')
                    # Delete the last file in order to don't create confusion
                    os.remove(PCR_result_file[-1])
                    return {"status": True, "res": read}, 200
                # return {"status": True, "res": ":)"}, 200
        else:
            with CheckFlag.lock:
                try:
                    rv = requests.get("http://{}:8080/log".format(Args().ip))
                except requests.exceptions.ConnectionError:
                    print("connection error")
                else:
                    print(rv)
                    if rv.status_code == 200:
                        CheckFunction.bak(rv.json())
                finally:
                    output = CheckFunction.bak()
                if not BarcodeSingleton() and output.get("external", False):
                    BarcodeSingleton.reset(gui_user_input(simpledialog.askstring, title="Barcode", prompt="Input barcode of exiting rack"))
            
            # RITORNA LO STATO E LO STAGE AL WEBINTERFACE
            return {
                       "status": False,
                       "res": "Status: {}\nStage: {}{}".format(
                           output.get("status", None),
                           output.get("stage", None),
                           "\n\n{}".format(output["msg"]) if output.get("msg", None) else ""
                       )
                   }, 200


# FUNZIONE DI PAUSA
# noinspection PyMethodMayBeStatic
class PauseFunction(Resource):
    def get(self):
        requests.get("http://{}:8080/pause".format(Args().ip))
        return {"status": False, "res": "Pausa"}, 200


# FUNZIONE DI RESUME
# noinspection PyMethodMayBeStatic
class ResumeFunction(Resource):
    @staticmethod
    def _resume():
        return requests.get("http://{}:8080/resume".format(Args().ip))
    
    @locked(CheckFlag.lock)
    def get(self):
        if BarcodeSingleton():
            while gui_user_input(simpledialog.askstring, title="Barcode", prompt="Input barcode of entering rack") != BarcodeSingleton():
                pass
            self._resume()
            time.sleep(1)
            BarcodeSingleton.reset()
        else:
            self._resume()
        return {"status": False, "res": "Resumed"}, 200
        

""" Copyright (c) 2020 Covmatic.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
 and associated documentation files (the "Software"), to deal in the Software without restriction,
  including without limitation the rights to use, copy, modify, merge, publish, distribute,
   sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies
 or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
"""
