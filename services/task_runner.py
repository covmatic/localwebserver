from database import session
from models.protocols import Protocol
from datetime import timedelta, datetime
from timeloop import Timeloop
# from utils import secure_load_opentrons_module
import paramiko as pk
from scp import SCPClient
import json
import time
import subprocess
from os import environ

PCR_API_NAME = 'BioRad.Example_Application.exe'
PCR_PATH = 'C:/Users/inse9/OneDrive/Desktop/Bio-Rad CFX API v1.1'
OT2_SSH_KEY = './ot2_ssh_key'
OT2_PROTOCOL_PATH = '/var/lib/jupyter/notebooks'
# TODO: Put the names in a json file and read the filenames
OT2_PROTOCOL_FILE = 'new_protocol.py'  # For stations in general keep protocol name constant.
OT2_PROTOCOLBP1_FILE = 'protocol_B_part1.py'
OT2_PROTOCOLBP2_FILE = 'protocol_B_part2.py'
OT2_PROTOCOLBP3_FILE = 'protocol_B_part3.py'
# FIXME: Decide how to differentiate the 2 lines of station A i.e: P300 or P1000
OT2_PROTOCOL1V1_FILE = 'protocol_A_part1.py'  # Pre-incubation Protocol for station A Purebase P1000S
OT2_PROTOCOL1V2_FILE = 'protocol_A_part1.py'  # Pre-incubation Protocol for station A Purebase P1000S
OT2_PROTOCOL2V1_FILE = 'protocol_A_part2.py'
OT2_PROTOCOL2V2_FILE = 'protocol_A_part2.py'
OT2_TEMP_PROTOCOL_FILE = 'set_temp.py'
OT2_REMOTE_LOG_FILEPATH = '/var/lib/jupyter/notebooks/outputs/completion_log.json'
# OT-2-IP is the name of environment variable in order to fix the IPs of the robot
OT2_TARGET_IP_ADDRESS = environ['OT-2-IP']
# OT2_TARGET_IP_ADDRESS = '10.213.55.63'
OT2_ROBOT_PASSWORD = 'opentrons'
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
    local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
    scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
    scp_client.close()
    return local_filepath


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
            if action == "settemp":
                print("station 1 is setting the temperature module!")
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
                # TODO: Check the protocol
                print("station 1 is checking the current temperature matches target ")
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
                # TODO: Decide what we need to do with calibration
            elif action == "calibration":
                print("Calibrating")
                ####################################################################################
                time.sleep(2)
            else:
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
                        local_filepath = ssh_scp()
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
                    if action == 'Pre-Deepwell-Check':
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
                        code = channel.recv_exit_status()
                        print("I got the code: {}".format(code))
                        local_filepath = ssh_scp()
                    else:
                        print('Action Not Defined')
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
                elif station == 3:  # station C
                    print("Performing Protocol")  # for Debugging
                    ####################################################################################
                    client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                    channel = client.invoke_shell()
                    channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOL_FILE))
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
            if action != 'calibration' and action != "PCR":
                with open(local_filepath) as f:
                    data = json.load(f)
                    stat = data["stages"][-1]["status"]
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
            print(protocol.status)
        except Exception as e:
            protocol.set_failed()
            session.add(protocol)
            session.commit()
            print(e)
