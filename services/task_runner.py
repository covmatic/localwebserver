from database import session
from models.protocols import Protocol
from datetime import timedelta, datetime
from timeloop import Timeloop
# from utils import secure_load_opentrons_module
import paramiko as pk
from scp import SCPClient, SCPException
import json
# import time
import subprocess
import os
from os import environ
from gui.args import Args


# PCR API name and path
if not Args().__dict__:
    Args.parse("Task runner.")
if not os.path.exists(Args().ssh_key):
    raise FileNotFoundError("Cannot find SSH key file '{}'".format(Args().ssh_key))


TASK_QUEUE_POLLING_INTERVAL = 5
# TASK_RUNNING = False
app = object()
scheduler = Timeloop()


def print_info():
    print("Target Opentrons IP: {}".format(Args().ip))


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
    

def create_ssh_client(usr, key_file, pwd):
    client = pk.SSHClient()  # Create an object SSH client
    client.set_missing_host_key_policy(pk.AutoAddPolicy())  # It is needed to add the device policy
    client.connect(Args().ip, username=usr, key_filename=key_file, password=pwd)
    return client


def ssh_scp():
    client = create_ssh_client(usr=Args().user, key_file=Args().ssh_key, pwd=Args().pwd)
    name_filepath = Args().log_local.format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
    
    try:
        scp_client = SCPClient(client.get_transport())
        scp_client.get(remote_path=Args().log_remote, local_path=name_filepath)
    except SCPException as e:
        print("Error retrieving remote logfile")
        print("{}".format(e))
    finally:
        scp_client.close()
    
    return name_filepath


def start_scheduler(app_ctx):
    global app
    app = app_ctx
    scheduler.start(block=False)


@scheduler.job(interval=timedelta(seconds=5))
def check_new_tasks():
    # print("Checking new tasks")
    protocol = Protocol.query.filter_by(status="queued").first()
    if protocol is not None:
        protocol.set_running()
        session.add(protocol)
        session.commit()
        try:
            station = protocol.station
            action = protocol.action
            if station == 1:  # station A     V1 = Purebase P1000S    V2 = Purebase P300S
                if action == "stationA":  # Purebase P1000S
                    print("Performing Pre-Incubation Protocol V1")  # For Debugging
                    ####################################################################################
                    client = create_ssh_client(usr=Args().user, key_file=Args().ssh_key, pwd=Args().pwd)
                    channel = client.invoke_shell()
                    channel.send('opentrons_execute {} -n \n'.format(Args().protocol_remote))
                    channel.send('exit \n')
                    code = channel.recv_exit_status()
                    print("I got the code: {}".format(code))
                    # SCP Client takes a paramiko transport as an argument
                    local_filepath = ssh_scp()
                else:
                    print("Action not defined")
            elif station == 2:  # station B
                print("Performing Protocol")  # For Debugging
                ###################################################################################
                if action == "stationB":
                    client = create_ssh_client(usr=Args().user, key_file=Args().ssh_key, pwd=Args().pwd)
                    channel = client.invoke_shell()
                    channel.send('opentrons_execute {} -n \n'.format(Args().protocol_remote))
                    channel.send('exit \n')
                    code = channel.recv_exit_status()
                    print("I got the code: {}".format(code))
                    local_filepath = ssh_scp()
                else:
                    print('Action Not Defined')
            elif station == 3:  # station C
                print("Performing Protocol")  # for Debugging
                ####################################################################################
                client = create_ssh_client(usr=Args().user, key_file=Args().ssh_key, pwd=Args().pwd)
                channel = client.invoke_shell()
                channel.send('opentrons_execute {} -n \n'.format(Args().protocol_remote))
                channel.send('exit \n')
                code = channel.recv_exit_status()
                print("I got the code: {}".format(code))
                local_filepath = ssh_scp()
            elif station == 4:  # PCR
                if action == "PCR":
                    subprocess.call(Args().pcr_app)
                else:
                    print("Action not defined")
            else:
                print("Station not defined ! ")
            protocol.set_completed()
            session.add(protocol)
            session.commit()
            # Reading of the current stages in the Opentrons protocols
            if action != "PCR":
                with open(local_filepath, 'r') as f:
                    data = json.load(f)
                    # Nuovo formato di log
                    stat = data["status"]
                    # stat = data["stages"][-1]["status"]
                if "FAILED" in stat:
                    print("Protocol Failed")
                    protocol.set_failed()
                else:
                    protocol.set_completed()
                    session.add(protocol)
                    session.commit()
            else:
                protocol.set_completed()
                session.add(protocol)
                session.commit()
            # for debug
            print(protocol.status)
        except Exception as e:
            protocol.set_failed()
            session.add(protocol)
            session.commit()
            print(e)


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
