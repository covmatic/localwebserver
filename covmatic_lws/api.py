"""LocalWebServer API"""
import requests
from requests.auth import HTTPDigestAuth
from flask_restful import Resource
from flask import request
import glob
import os
from shutil import copy2
import json

from scp import SCPException

from .args import Args
from .task_runner import Task, StationTask, task_fwd_queue, task_bwd_queue, task_finished_queue, YumiTask
import threading
from .utils import SingletonMeta, locked, acquire_lock
from flask_restful import Api
import logging
from .ssh import SSHClient, copy_file_ssh
import time
import base64
import queue


class LocalWebServerAPI(Api):
    def __init__(self, prefix=Args().api_prefix, *args, **kwargs):
        super(LocalWebServerAPI, self).__init__(*args, prefix=prefix, **kwargs)
        self.add_resource(TaskFunction, '/<int:station>/<string:action>')
        self.add_resource(CheckFunction, '/check')
        self.add_resource(PauseFunction, '/pause')
        self.add_resource(ResumeFunction, '/resume')
        self.add_resource(LogFunction, '/log')
        self.add_resource(YumiBarcodeOK, '/0/OK')
        self.add_resource(YumiBarcodeNO, '/0/NO')
        self.add_resource(YumiStart, '/0/YuMistart')
        self.add_resource(YumiStop, '/0/YuMistop')
        self.add_resource(YumiPPtoMain, '/0/YumiPPtoMain')


class LogFunction(Resource):
    lock = threading.Lock()

    def post(self):
        try:
            s = request.data.decode('utf-8')
        except UnicodeDecodeError:
            s = request.get_data(as_text=True)
        logging.getLogger().info(s)


class TaskFunction(Resource):
    def get(self, station, action):
        try:
            t = Task(station, action)
            t.start()
        except (Task.TaskRunningException, KeyError) as e:
            logging.getLogger().info(e)
            return {
                       "status": "failed",
                       "message": str(e)
            }, 422
        else:
            CheckFunction.bak({})
            return {"status": False, "message": "Started {}".format(t)}, 201

class CheckFunction(Resource):
    bak_lock = threading.Lock()
    _bak = {}

    @property
    def logger(self) -> logging.getLoggerClass():
        return logging.getLogger(type(self).__name__)

    @classmethod
    @locked(bak_lock)
    def bak(cls, value=None):
        if value is not None:
            cls._bak = value
        return cls._bak

    log_endpoint = "http://{}:8080/log".format(Args().ip)

    def get(self):
        # Get enqueued content to forward, if any
        # TODO for now we return element-by-element
        #      the dashboard should be implemented the accept a list as a result first
        try:
            j = task_fwd_queue.get(block=False)
        except queue.Empty:
            pass
        else:
            self.logger.info("Check: found results on queue, returning {}".format(j))
            return j

        with Task.lock:
            task_running = Task.running
            task_type = Task.type
            task_str = str(Task._running)
        if task_running:
            self.logger.debug("{} is running".format(task_str))
            if issubclass(task_type, StationTask):
                try:
                    rv = requests.get(self.log_endpoint, timeout=2)
                except Exception as e:
                    self.logger.info("{} - {}".format(self.log_endpoint, type(e).__name__))
                else:
                    self.logger.info("{} - Status Code {}".format(self.log_endpoint, rv.status_code))
                    self.logger.debug(rv.content.decode('ascii'))
                    if rv.status_code == 200:
                        CheckFunction.bak(rv.json())
                finally:
                    output = CheckFunction.bak()
                return {
                           "status": False,
                           "res": "Status: {}\nStage: {}{}".format(
                               output.get("status", None),
                               output.get("stage", None),
                               "\n\n{}".format(output["msg"]) if output.get("msg", None) else ""
                           ),
                           "runinfo": {
                               "status": output.get("status", None),
                               "stage": output.get("stage", None),
                               "msg": output["msg"] if output.get("msg", None) else "",
                               "external": output.get("external", False),
                               "dashboard_input": output.get("dashboard_input", False)
                           }
                       }, 200
            elif issubclass(task_type, YumiTask):
                return {
                           "status": False,
                           "res": "Waiting for barcode..."
                       }, 200
            else:
                return {"status": False, "res": task_str}, 200

        else:
            self.logger.debug("No task is running")
            with Task.lock:
                code = Task.exit_code
                Task.exit_code = None
            if code is None:
                # No station protocol was running, look for PCR result files
                pcr_result_files = sorted(glob.glob(Args().pcr_results), key=os.path.getctime, reverse=True)
                if pcr_result_files:
                    self.logger.debug("Found PCR files: {}".format(pcr_result_files))
                    try:
                        with open(str(pcr_result_files[0]), 'r', encoding='utf-8-sig') as f:
                            result = json.load(f)
                    except Exception as e:
                        return {"status": True, "res": str(e)}, 500
                    output = {"result": result}
                    # Look for pcrd file
                    pcrd_filename = os.path.basename(
                        pcr_result_files[0]
                    ).split("_", maxsplit=1)[-1][:-12]  # .split(...)[-1] -> remove leading serial number, [:-12] remove trailing '_Result.json'
                    pcrd_filename = os.path.join(Args().pcr_pcrd, pcrd_filename + ".pcrd")
                    if os.path.isfile(pcrd_filename):
                        self.logger.debug("Matching pcrd file found: {}".format(pcrd_filename))
                        try:
                            with open(pcrd_filename, 'rb') as pcrd_f:
                                pcrd_s = base64.b64encode(pcrd_f.read()).decode('ascii')
                        except Exception as e:
                            self.logger.warning("Error while encoding pcrd file '{}':\n{}".format(pcrd_filename, str(e)))
                        else:
                            output["pcrd"] = pcrd_s
                    else:
                        self.logger.warning("No matching pcrd file found: {}".format(pcrd_filename))
                    # Make a backup of the PCR results
                    os.makedirs(Args().pcr_backup, exist_ok=True)
                    copy2(pcr_result_files[0], Args().pcr_backup)
                    # Delete the last file in order to not create confusion
                    os.remove(pcr_result_files[0])
                    return {"status": True, "res": output}, 200
                else:
                    self.logger.debug("No Protocol nor Result available")
                    return {"message": "No Protocol nor Result available"}, 404
            else:
                # Station protocol has just ended, reset backup
                res = "Failed" if code else "Completed"
                self.logger.info("Protocol {}: exit code {}".format(res.lower(), code))
                if Args().log_local:
                    log_remote = CheckFunction.bak().get("runlog", None)
                    log_local = Args().log_local.format(time.strftime("%Y_%m_%d__%H_%M_%S"))
                    if log_remote:
                        try:
                            copy_file_ssh(log_remote, log_local)
                        except Exception as e:
                            self.logger.warning("Could not copy runlog from '{}' to '{}':\n{}".format(log_remote, log_local, e))
                        else:
                            self.logger.info("Copied runlog from '{}' to '{}'".format(log_remote, log_local))
                exception_log_filepath = CheckFunction.bak().get('exceptionlog', None)
                CheckFunction.bak({})
                if code:
                    return {"message": "Protocol execution {} with exit code: {}. Message: {}".format(
                                            res,
                                            code,
                                            self.get_error_from_remote_exception_file(exception_log_filepath))
                            }, 503
                return {"status": True, "res": res, "exit_code": code}, 200

    def get_error_from_remote_exception_file(self, remote_exception_log_filepath: str) -> str:
        if remote_exception_log_filepath:
            filename = os.path.basename(os.path.normpath(remote_exception_log_filepath))
            temp_path = os.path.join(Args().temp_data_dir, filename)
            self.logger.debug("Copying to temporary file: {}".format(temp_path))
            try:
                copy_file_ssh(remote_exception_log_filepath, temp_path)
            except SCPException as e:
                self.logger.error("Error copying file {} to {}: {}".format(remote_exception_log_filepath, temp_path, e))
            else:
                self.logger.info("Copied {} to {}".format(remote_exception_log_filepath, temp_path))
                with open(temp_path, 'r') as f:
                    error = json.load(f).get('error', None)
                # os.remove(temp_path)
                return error
        self.logger.error("Remote error filename is empty.")
        return "unknown; see error file on robot."

class PauseFunction(Resource):
    def get(self):
        try:
            requests.get("http://{}:8080/pause".format(Args().ip))
        except Exception as e:
            r = {"status": False, "res": str(e)}, 500
        else:
            r = {"status": False, "res": "Pausa"}, 200
        return r


class ResumeFunction(Resource):
    @property
    def logger(self) -> logging.getLoggerClass():
        return logging.getLogger(type(self).__name__)

    def _resume(self):
        self.logger.debug("Resuming")
        try:
            requests.get("http://{}:8080/resume".format(Args().ip))
        except Exception as e:
            r = {"status": False, "res": str(e)}, 500
        else:
            r = {"status": False, "res": "Resumed"}, 200
        return r

    def get(self):
        return self._resume()


class YumiBarcodeOK(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self):
        # emptying queue
        logging.info("Got YES answer from dashboard!")
        with task_finished_queue.mutex:
            task_finished_queue.queue.clear()

        if Task.running:
            # Mette in coda "OK"
            task_bwd_queue.put("OK")
            # Aspetta che il task abbia finito prima di ritornare
            try:
                logging.info("Waiting Task closed")
                task_finished_queue.get(timeout=600)
                logging.info("Task closed, returning from OK...")
            except queue.Empty:
                logging.error("No CLOSED answer returned from task!")
                return {"status": False, "res": ""}, 504
            return {"status": False, "res": "OK"}, 200
        return {"status": False, "res": ""}, 500


class YumiBarcodeNO(Resource):
    # noinspection PyMethodMayBeStatic
    def get(self):
        logging.info("Got NO answer from dashboard!")
        # emptying queue
        with task_finished_queue.mutex:
            task_finished_queue.queue.clear()

        # Mette in coda "NO"
        task_bwd_queue.put("NO")

        if Task.running:
            # Aspetta che il task abbia finito prima di ritornare
            try:
                logging.info("Waiting Task closed")
                task_finished_queue.get(timeout=600)
                logging.info("Task closed, returning from NO...")
            except queue.Empty:
                logging.error("No CLOSED answer returned from task!")
                return {"status": False, "res": ""}, 504
            return {"status": False, "res": "OK"}, 200
        return {"status": False, "res": ""}, 500


class YumiStart(Resource):
    def __init__(self):
        # Controller IP
        self.hostname = 'http://192.168.125.1'
        self.start_url = '/rw/rapid/execution?action=start'
        # Parameters for starting all the tasks of the Yumi
        self.start_payload = {'regain': 'continue', 'execmode': 'continue', 'cycle': 'once',
                              'condition': 'none', 'stopatbp': 'disabled', 'alltaskbytsp': 'true'}

    def get(self):
        try:
            logging.info("Starting request to {}.".format(self.hostname + self.start_url))
            start = requests.post(self.hostname + self.start_url,
                                  auth=HTTPDigestAuth("Default User", "robotics"),
                                  data=self.start_payload)
            if start.status_code == 400:
                # It should answers the controller with the error if any
                logging.warning("Execution error")
                # Only connection error -> Probably this will merge in a >= condition.
            elif start.status_code > 400:
                logging.warning("Connection error, Status code: {}".format(start.status_code))
            logging.info("Status code: {}".format(start.status_code))
            r = {"status": False, "res": "Ok"}, 200
        except requests.exceptions.ConnectionError as err:
            logging.warning("Connection error {}".format(err))
            r = {"status": False, "res": str(err)}, 500
        except Exception as err:
            logging.error("{}".format(err))
            r = {"status": False, "res": str(err)}, 500
        return r


class YumiStop(Resource):
    def __init__(self):
        # Controller IP
        self.hostname = 'http://192.168.125.1'
        self.start_url = '/rw/rapid/execution?action=stop'
        # Parameters for stopping all the tasks of the Yumi
        self.start_payload = {'stopmode': 'stop', 'usetsp': 'normal'}

    def get(self):
        try:
            logging.info("Starting request to {}.".format(self.hostname + self.start_url))
            stop = requests.post(
                self.hostname + self.start_url,
                auth=HTTPDigestAuth("Default User", "robotics"),
                data=self.start_payload)
            if stop.status_code == 400:
                # It should answers the controller with the error if any
                logging.warning("Execution error")
                # Only connection error -> Probably this will merge in a >= condition.
            elif stop.status_code > 400:
                logging.warning("Connection error, Status code: {}".format(stop.status_code))
            logging.info("Status code: {} ".format(stop.status_code))
            r = {"status": False, "res": "Ok"}, 200
        except requests.exceptions.ConnectionError as err:
            logging.warning("Connection error {}".format(err))
            r = {"status": False, "res": str(err)}, 500
        except Exception as err:
            logging.error("{}".format(err))
            r = {"status": False, "res": str(err)}, 500
        return r

class YumiPPtoMain(Resource):
    # Resetta il puntatore di programma al main (inizio del programma)
    # Va chiamato dopo uno STOP.
    def __init__(self):
        # Controller IP
        self.hostname = 'http://192.168.125.1'
        self.start_url = '/rw/rapid/execution?action=resetpp'

    def get(self):
        try:
            logging.info("Starting request to {}.".format(self.hostname + self.start_url))
            PPtoMain = requests.post(
                self.hostname + self.start_url,
                auth=HTTPDigestAuth("Default User", "robotics")
            )
            if PPtoMain.status_code == 400:
                # It should answers the controller with the error if any
                logging.warning("Execution error")
                # Only connection error -> Probably this will merge in a >= condition.
            elif PPtoMain.status_code > 400:
                logging.warning("Connection error, Status code: {}".format(PPtoMain.status_code))
            logging.info("Status code: {} ".format(PPtoMain.status_code))
            r = {"status": False, "res": ""}, PPtoMain.status_code
        except requests.exceptions.ConnectionError as err:
            logging.warning("Connection error {}".format(err))
            r = {"status": False, "res": str(err)}, 500
        except Exception as err:
            logging.error("{}".format(err))
            r = {"status": False, "res": str(err)}, 500
        return r




# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
