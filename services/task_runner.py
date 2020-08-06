from database import session
from models.protocols import Protocol
from datetime import timedelta, datetime
from timeloop import Timeloop
# from utils import secure_load_opentrons_module
import paramiko as pk
from scp import SCPClient
import time
import subprocess


OT2_SSH_KEY = './ot2_ssh_key'
OT2_PROTOCOL_PATH = '/var/lib/jupyter/notebooks'
# TODO: Put the names in a json file and read the filenames
OT2_PROTOCOL_FILE = 'new_protocol.py'  # For stations in general keep protocol name constant.
OT2_PROTOCOL1V1_FILE = 'v1_station_A1_p1000.py'  # Pre-incubation Protocol for station A Purebase P1000S
OT2_PROTOCOL1V2_FILE = 'v1_station_A1_p1000.py'  # Pre-incubation Protocol for station A Purebase P1000S
OT2_PROTOCOL2V1_FILE = 'v1_station_A2_p1000.py'
OT2_PROTOCOL2V2_FILE = 'v1_station_A2_p1000.py'
OT2_TEMP_PROTOCOL_FILE = 'set_temp.py'
OT2_REMOTE_LOG_FILEPATH = '/var/lib/jupyter/notebooks/outputs/completion_log.json'
OT2_TARGET_IP_ADDRESS = '10.213.55.232'
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
            # Call your code using execute_automation()
            # execute_automation()
            # module = secure_load_opentrons_module(
            #     module_name=protocol.protocol_type.module_name,
            #     file_path=app.config["OT2_MODULES_PATH"],
            #     filename=protocol.protocol_type.filename,
            #     checksum=protocol.protocol_type.checksum,
            #     verify=False
            # )
            # otm = module.OpenTronsModule(
            #     usr=app.config["OT2_ROBOT_USER"],
            #     pwd=app.config["OT2_ROBOT_PASSWORD"],
            #     key_file=app.config["OT2_SSH_KEY"],
            #     target_ip=app.config["OT2_TARGET_IP_ADDRESS"],
            #     protocol_path=app.config["OT2_PROTOCOL_PATH"],
            #     protocol_file=app.config["OT2_PROTOCOL_FILE"],
            #     remote_path=app.config["OT2_REMOTE_LOG_FILEPATH"]
            # )
            # # Call your routine here
            # otm.test_import()
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
                # SCP Client takes a paramiko transport as an argument
                client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                scp_client = SCPClient(client.get_transport())
                local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                scp_client.close()
                ####################################################################################
            elif action == "checktemp":  # For testing this is the same as set temp
                # TODO: Check the protocol
                print("station 1 is checking the current temperature matches target ")
                ###################################################################################
                client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                channel = client.invoke_shell()
                channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_TEMP_PROTOCOL_FILE))
                channel.send('exit \n')
                code = channel.recv_exit_status()
                print("I got the code: {}".format(code))
                # SCP Client takes a paramiko transport as an argument
                client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                scp_client = SCPClient(client.get_transport())
                local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                scp_client.close()
                ####################################################################################
            elif action == "calibration":
                print("Calibrating")
                ####################################################################################
                time.sleep(5)
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
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        scp_client = SCPClient(client.get_transport())
                        local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                        scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                        scp_client.close()
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
                        # SCP Client takes a paramiko transport as an argument
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        scp_client = SCPClient(client.get_transport())
                        local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                        scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                        scp_client.close()
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
                        # SCP Client takes a paramiko transport as an argument
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        scp_client = SCPClient(client.get_transport())
                        local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                        scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                        scp_client.close()
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
                        # SCP Client takes a paramiko transport as an argument
                        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                        scp_client = SCPClient(client.get_transport())
                        local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                        scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                        scp_client.close()
                    else:
                        print("Action not defined")
                elif station == 2:  # station B
                    print("Performing Protocol")  # For Debugging
                    ####################################################################################
                    client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                    # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                    channel = client.invoke_shell()
                    channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOL_FILE))
                    channel.send('exit \n')
                    code = channel.recv_exit_status()
                    print("I got the code: {}".format(code))
                    # SCP Client takes a paramiko transport as an argument
                    client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                    scp_client = SCPClient(client.get_transport())
                    local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                    scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                    scp_client.close()
                elif station == 3:  # station C
                    print("Performing Protocol")  # for Debugging
                    ####################################################################################
                    client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                    # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
                    channel = client.invoke_shell()
                    channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_PROTOCOL_FILE))
                    channel.send('exit \n')
                    code = channel.recv_exit_status()
                    print("I got the code: {}".format(code))
                    # SCP Client takes a paramiko transport as an argument
                    client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
                    scp_client = SCPClient(client.get_transport())
                    local_filepath = "./log_{}.json".format(datetime.now().strftime("%m-%d-%Y_%H_%M_%S"))
                    scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=local_filepath)
                    scp_client.close()
                elif station == 4:  # PCR
                    if action == "PCR":
                        subprocess.call('PCR_api.exe')
                    else:
                        print("Action not defined")
                else:
                    print("Station not defined ! ")
            protocol.set_completed()
            session.add(protocol)
            session.commit()
        except Exception as e:
            protocol.set_failed()
            session.add(protocol)
            session.commit()
            print(e)
