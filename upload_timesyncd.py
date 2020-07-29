"""Program for substituting the file for the sync of the date of the machine"""

import paramiko as pk
from scp import SCPClient

local_filepath = 'C:/Users/inse9/'
remote_filepath = '/etc/systemd/'
filename = 'timesyncd.conf'
key_name = 'ot2_ssh_key'  # Key name
key = local_filepath + key_name
cmd_rw = 'mount -o remount, rw /'
local_file = local_filepath + filename


def main(ip='192.168.1.14'):  # It creates the connection: you need to pass only the ip
    client = pk.SSHClient()
    client.set_missing_host_key_policy(pk.AutoAddPolicy())  # It is needed to add the device policy
    client.connect(ip, username='root', key_filename=key, password='opentrons')  # Connection
    print('Access done!')
    client.exec_command(cmd_rw)  # It allows to modify the file system
    print('permission of files modified!')
    scp_client = SCPClient(client.get_transport())  # It opens the channel for the scp connection
    scp_client.put(local_file, remote_filepath)  # It copies the file
    scp_client.close()
    print('Completed!')


if __name__ == '__main__':
    main()
