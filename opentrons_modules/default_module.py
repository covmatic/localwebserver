from scp import SCPClient
from datetime import datetime
import paramiko as pk
import time


class OpenTronsModule(object):

    def __init__(self, usr, key_file, pwd, target_ip, protocol_path, protocol_file, remote_path):
        self.usr = usr
        self.key_file = key_file
        self.pwd = pwd
        self.target_ip = target_ip
        self.command = 'opentrons_execute {}/{} -n \n'.format(protocol_path, protocol_file)
        self.remote_path = protocol_file,
        self.remote_path = remote_path

    def create_ssh_client(self):
        client = pk.SSHClient()  # Create an object SSH client
        client.set_missing_host_key_policy(pk.AutoAddPolicy())  # It is needed to add the device policy
        client.connect(
            self.target_ip,
            username=self.usr,
            key_filename=self.key_file,
            password=self.pwd
        )
        return client

    def create_scp_client(self):
        client = self.create_ssh_client()
        return SCPClient(client.get_transport())

    @staticmethod
    def test_import():
        for i in range(0,5):
            print("If you can read this, you've successfully imported me!")
            time.sleep(1)


class MyOpenTronsModule(OpenTronsModule):

    def run(self):
        self.command = 'station_a'
        client = self.create_ssh_client()
        channel = client.invoke_shell()
        channel.send(self.command)
        channel.send('exit \n')
        code = channel.recv_exit_status()
        # Create new ssh channel for scp operations
        scp_client = self.create_scp_client()
        timestamp = datetime.now().strftime("%m-%d-%Y_%H_%M_%S")
        local_filepath = "./log_{}.json".format(timestamp)
        scp_client.get(remote_path=self.remote_path, local_path=local_filepath)
        scp_client.close()
        return code

    def run(self):
        print("If you can read this, you've successfully imported me!")
