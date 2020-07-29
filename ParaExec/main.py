from config import (
    host,
    user,
    ssh_key_filepath,
    local_file_directory,
    remote_path
)
from .files import fetch_local_files
from .client import RemoteClient

key_name = 'ot2_ssh_key'
direct = 'C:/Users/inse9/'
key = direct + key_name
protocol_folder = '/var/lib/jupyter/notebooks/'
protocol_file = 'v1_station_C.py'

def main():
    """Initialize remote host client and execute actions."""
    remote = RemoteClient(host, user, ssh_key_filepath, remote_path)
    #upload_files_to_remote(remote)
    execute_command_on_remote(remote)
    remote.disconnect()


def upload_files_to_remote(remote):
    """Upload files to remote via SCP."""
    local_files = fetch_local_files(local_file_directory)
    remote.bulk_upload(local_files)

def download_files_to_remote(remote):
    """Download files from remote via SCP."""
    local_files = 'FILENAME'
    remote.download_file(local_files)


def execute_command_on_remote(remote):
    """Execute UNIX command on the remote host."""
    remote.execute_cmd(['export OT_SMOOTHIE_ID="AMA"','RUNNING_ON_PI="true"','opentrons_execute {}/{} -n'.format(protocol_folder, protocol_file)])

if __name__ == "__main__":
    main()
