from database import session
# from flask import jsonify
import requests
import tkinter as tk
from flask_restful import Resource
from flask_restful import reqparse
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
from services.task_runner import OT2_TARGET_IP_ADDRESS
import threading


# from services.task_runner import OT2_SSH_KEY, OT2_ROBOT_PASSWORD, OT2_REMOTE_LOG_FILEPATH


PCR_result_file_scheme = '????????_Data_??-??-????_??-??-??_Result.json'
PCR_results_path = 'C:/PCR_BioRad/json_results/'


def gui_user_input(f, *args, **kwargs):
    root = tk.Tk()
    root.withdraw()
    root.call('wm', 'attributes', '.', '-topmost', True)
    root.lift()
    root.attributes('-topmost', True)
    s = f(*args, **kwargs)
    root.destroy()
    return s


class SingletonMeta(type):
    def __new__(meta, name, bases, classdict):
        def new(cls, code: Optional[Any] = None):
            if cls._inst is None:
                cls._inst = None if code is None else super(getattr(os.sys.modules[__name__], name), cls).__new__(cls, code)
            return cls._inst
        
        classdict["__new__"] = classdict.get("__new__", new)
        return super(SingletonMeta, meta).__new__(meta, name, bases, classdict)
    
    def __init__(cls, name, bases, classdict):
        super(SingletonMeta, cls).__init__(name, bases, classdict)
        cls._inst = None
    
    def reset(cls, code: Optional[Any] = None):
        del cls._inst
        cls._inst = None
        if code is not None:
            cls._inst = cls(code)
        return cls._inst


class BarcodeSingleton(str, metaclass=SingletonMeta):
    pass


class CheckFlag:
    lock = threading.Lock()


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
    def get(self):
        with CheckFlag.lock:
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
                    PCR_result_file = glob.glob(PCR_results_path + PCR_result_file_scheme)
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
                while True:
                    try:
                        rv = requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/log")
                    except requests.exceptions.ConnectionError:
                        time.sleep(0.5)
                    else:
                        break
                output = rv.json()
                print(rv)
    
                # RITORNA LO STATO E LO STAGE AL WEBINTERFACE
                if BarcodeSingleton() is None and output["external"]:
                    BarcodeSingleton(gui_user_input(simpledialog.askstring, title="Barcode", prompt="Input barcode of exiting rack"))
                return {
                           "status": False,
                           "res": "Status: {}\nStage: {}{}".format(
                               output["status"],
                               output["stage"],
                               "\n\n{}".format(output["msg"]) if output["msg"] else ""
                           )
                       }, 200


# FUNZIONE DI PAUSA
# noinspection PyMethodMayBeStatic
class PauseFunction(Resource):

    def get(self):
        requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/pause")
        return {"status": False, "res": "Pausa"}, 200


# FUNZIONE DI RESUME
# noinspection PyMethodMayBeStatic
class ResumeFunction(Resource):
    def get(self):
        with CheckFlag.lock:
            if BarcodeSingleton() is not None:
                while gui_user_input(simpledialog.askstring, title="Barcode", prompt="Input barcode of entering rack") != BarcodeSingleton():
                    pass
                BarcodeSingleton.reset()
            requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/resume")
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
