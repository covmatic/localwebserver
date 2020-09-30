from database import session
from models.protocols import Protocol
from datetime import timedelta, datetime
from timeloop import Timeloop
# from utils import secure_load_opentrons_module
import paramiko as pk
from scp import SCPClient
import json
# import time
import subprocess
from os import environ

# PCR API name and path
PCR_API_NAME = 'BioRad.Example_Application.exe'
PCR_PATH = 'C:/PCR_BioRad/APIs/BioRad_CFX_API_v1.4/'
OT2_SSH_KEY = './ot2_ssh_key'
# Path of the protocols inside the Robots
OT2_PROTOCOL_PATH = '/var/lib/jupyter/notebooks'
# Protocol namefiles
# TODO: Put the names in a json file and read the filenames
OT2_PROTOCOLC_FILE = 'station_c.py'  # For stations in general keep protocol name constant.
OT2_PROTOCOLBP1_FILE = 'protocol_B_part1.py'
OT2_PROTOCOLBP2_FILE = 'protocol_B_part2.py'
OT2_PROTOCOLBP3_FILE = 'protocol_B_part3.py'
# FIXME: Decide how to differentiate the 2 lines of station A i.e: P300 or P1000
OT2_PROTOCOL1V1_FILE = 'protocol_A_part1.py'  # Pre-incubation Protocol for station A Purebase P1000S
OT2_PROTOCOL1V2_FILE = 'protocol_A_part1.py'  # Pre-incubation Protocol for station A Purebase P1000S
OT2_PROTOCOL2V1_FILE = 'protocol_A_part2.py'
OT2_PROTOCOL2V2_FILE = 'protocol_A_part2.py'  # it should be for the BP Genomics
OT2_TEMP_PROTOCOL_FILE = 'set_temp.py'
OT2_REMOTE_LOG_FILEPATH = '/var/lib/jupyter/notebooks/outputs/completion_log.json'
# OT-2-IP is the name of environment variable in order to fix the IPs of the robot
# OT2_TARGET_IP_ADDRESS = environ['OT-2-IP']
OT2_TARGET_IP_ADDRESS = '169.254.232.63'  # Only for debugging
OT2_ROBOT_PASSWORD = 'opentrons'  # Opentrons password of the ssh key
TASK_QUEUE_POLLING_INTERVAL = 5
# TASK_RUNNING = False

app = object()
scheduler = Timeloop()


def create_ssh_client(usr, key_file, pwd):
    client = pk.SSHClient()  # Create an object SSH client
    client.set_missing_host_key_policy(pk.AutoAddPolicy())  # It is needed to add the device policy
    client.connect(OT2_TARGET_IP_ADDRESS, username=usr, key_filename=key_file, password=pwd)
    return client


def ssh_scp():
    client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
    scp_client = SCPClient(client.get_transport())
    name_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
    scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=name_filepath)
    scp_client.close()
    return name_filepath


def start_scheduler(app_ctx):
    global app
    app = app_ctx
    scheduler.start(block=False)


@scheduler.job(interval=timedelta(seconds=5))
def check_new_tasks():
    # print("Checking new tasks")
    # FIXME: CHECK IF THE GLOBAL local_filepath works!!
    global local_filepath
    protocol = Protocol.query.filter_by(status="queued").first()
    if protocol is not None:
        protocol.set_running()
        session.add(protocol)
        session.commit()
        try:
            station = protocol.station
            action = protocol.action
            if action == "settemp":
                print("The robot is setting the temperature module!")
                ###################################################################################
                client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                channel = client.invoke_shell()
                channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_TEMP_PROTOCOL_FILE))
                channel.send('exit \n')
                code = channel.recv_exit_status()
                print("I got the code: {}".format(code))
                local_filepath = ssh_scp()
                # # SCP Client takes a paramiko transport as an argument
                # client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                # scp_client = SCPClient(client.get_transport())
                # local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                # scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                # scp_client.close()
                ####################################################################################
            elif action == "checktemp":  # For testing this is the same as set temp
                print("The robot is checking the current temperature matches target ")
                client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                channel = client.invoke_shell()
                channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_TEMP_PROTOCOL_FILE))
                channel.send('exit \n')
                code = channel.recv_exit_status()
                print("I got the code: {}".format(code))
                local_filepath = ssh_scp()
                # # SCP Client takes a paramiko transport as an argument
                # client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                # scp_client = SCPClient(client.get_transport())
                # local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                # scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                # scp_client.close()
                ####################################################################################
            elif action == 'calibration':
                print('calibro')
            else:
                # FIXME: adjust these things of the name of the protocols A
                if station == 1:  # station A     V1 = Purebase P1000S    V2 = Purebase P300S
                    if action == "Pre-IncubationV1":  # Purebase P1000S
                        print("Performing Pre-Incubation Protocol V1")  # For Debugging
                        ####################################################################################
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                        channel = client.invoke_shell()
                        channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOL1V1_FILE))
                        channel.send('exit \n')
                        code = channel.recv_exit_status()
                        print("I got the code: {}".format(code))

                        # SCP Client takes a paramiko transport as an argument
                        # local_filepath = ssh_scp()
                        # client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        # scp_client = SCPClient(client.get_transport())
                        # local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                        # scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                        # scp_client.close()
                    elif action == "Post-IncubationV1":
                        print("Performing Post-Incubation Protocol V1")  # For Debugging
                        ####################################################################################
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                        channel = client.invoke_shell()
                        channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOL2V1_FILE))
                        channel.send('exit \n')
                        code = channel.recv_exit_status()
                        print("I got the code: {}".format(code))
                        local_filepath = ssh_scp()
                        # # SCP Client takes a paramiko transport as an argument
                        # client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        # scp_client = SCPClient(client.get_transport())
                        # local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                        # scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                        # scp_client.close()
                    elif action == "Pre-IncubationV2":
                        print("Performing Pre-Incubation Protocol V2")  # For Debugging
                        ####################################################################################
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                        channel = client.invoke_shell()
                        channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOL1V2_FILE))
                        channel.send('exit \n')
                        code = channel.recv_exit_status()
                        print("I got the code: {}".format(code))
                        local_filepath = ssh_scp()
                        # # SCP Client takes a paramiko transport as an argument
                        # client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        # scp_client = SCPClient(client.get_transport())
                        # local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                        # scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                        # scp_client.close()
                    elif action == "Post-IncubationV2":
                        print("Performing Post-Incubation Protocol V2")  # For Debugging
                        ####################################################################################
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                        channel = client.invoke_shell()
                        channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOL2V2_FILE))
                        channel.send('exit \n')
                        code = channel.recv_exit_status()
                        print("I got the code: {}".format(code))
                        local_filepath = ssh_scp()
                        # # SCP Client takes a paramiko transport as an argument
                        # client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        # scp_client = SCPClient(client.get_transport())
                        # local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                        # scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                        # scp_client.close()
                    else:
                        print("Action not defined")
                elif station == 2:  # station B
                    print("Performing Protocol")  # For Debugging
                    ###################################################################################
                    if action == "Pre-Deepwell-Check":
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        channel = client.invoke_shell()
                        channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOLBP1_FILE))
                        channel.send('exit \n')
                        code = channel.recv_exit_status()
                        print("I got the code: {}".format(code))
                        local_filepath = ssh_scp()
                    elif action == 'Pre-Incubation':
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        channel = client.invoke_shell()
                        channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOLBP2_FILE))
                        channel.send('exit \n')
                        code = channel.recv_exit_status()
                        print("I got the code: {}".format(code))
                        local_filepath = ssh_scp()
                    elif action == 'Post-Incubation':
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        channel = client.invoke_shell()
                        channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOLBP3_FILE))
                        channel.send('exit \n')
                        code = channel.recv_exit_status()
                        print("I got the code: {}".format(code))
                        local_filepath = ssh_scp()
                    else:
                        print('Action Not Defined')

                elif station == 3:  # station C
                    print("Performing Protocol")  # for Debugging
                    ####################################################################################
                    client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                    channel = client.invoke_shell()
                    channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOLC_FILE))
                    channel.send('exit \n')
                    code = channel.recv_exit_status()
                    print("I got the code: {}".format(code))
                    local_filepath = ssh_scp()
                    # # SCP Client takes a paramiko transport as an argument
                    # client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                    # scp_client = SCPClient(client.get_transport())
                    # local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                    # scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                    # scp_client.close()
                elif station == 4:  # PCR
                    if action == "PCR":
                        subprocess.call(PCR_PATH + PCR_API_NAME)
                    else:
                        print("Action not defined")
                else:
                    print("Station not defined ! ")
            protocol.set_completed()
            session.add(protocol)
            session.commit()
            # Reading of the current stages in the Opentrons protocols
            if action != 'calibration' and action != "PCR":
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
