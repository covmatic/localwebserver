from api.utils import SingletonMeta
import configargparse
import argparse
import os


class Args(argparse.Namespace, metaclass=SingletonMeta):
    @classmethod
    def parse(cls, description):
        parser = configargparse.ArgParser(description=description, default_config_files=[os.path.join(os.path.expanduser(d), "covmatic.conf") for d in ("~", ".")])
        parser.add_argument('-I', '--ip', metavar='address', type=str, required=True, help="the robot's IP address or hostname")
        parser.add_argument('-A', '--app', metavar='path', type=str, default="C:/Program Files/Opentrons/Opentrons.exe", help="the Opentrons App filepath")
        parser.add_argument('-S', '--station', metavar='name', type=str, default="A", help="the default station type")
        parser.add_argument('-L', '--lang', metavar='lang', type=str, default="ENG", help="the default message language")
        parser.add_argument('-K', '--ssh-key', metavar='file', type=str, default="./ot2_ssh_key", help="SSH key file path")
        parser.add_argument('-P', '--pwd', metavar='pwd', type=str, default="", help="the SSH key passphrase")
        parser.add_argument('-U', '--user', metavar='name', type=str, default="root", help="the SSH username")
        parser.add_argument('--barcode-port', metavar='port', type=int, default=5002, help="the barcode server port")
        parser.add_argument('--pcr-app', metavar="path", type=str, default="C:/PCR_BioRad/APIs/BioRad_CFX_API_v1.4/BioRad.Example_Application.exe", help="the PCR app filepath")
        parser.add_argument('--pcr-results', metavar="path", type=str, default="C:/PCR_BioRad/json_results/????????_Data_??-??-????_??-??-??_Result.json", help="the PCR results filepath (scheme)")
        parser.add_argument('--web-app', metavar='url', type=str, default="https://ec2-15-161-32-20.eu-south-1.compute.amazonaws.com/stations", help="the Web App URL")
        parser.add_argument('--icon-file', metavar='path', type=str, default="./Covmatic_Icon.jpg", help="local file path for Covmatic icon")
        parser.add_argument('--icon-url', metavar='url', type=str, default="https://covmatic.org/wp-content/uploads/2020/10/cropped-Favicon-180x180.jpg", help="remote URL for Covmatic icon")
        parser.add_argument('--logo-file', metavar='path', type=str, default="./Covmatic_Logo.png", help="local file path for Covmatic logo")
        parser.add_argument('--logo-url', metavar='url', type=str, default="https://covmatic.org/wp-content/uploads/2020/06/logo-1.png", help="remote URL for Covmatic logo")
        parser.add_argument('--log-remote', metavar='path', type=str, default="/var/lib/jupyter/notebooks/outputs/completion_log.json", help="remote file path for completion log file")
        parser.add_argument('--log-local', metavar='path', type=str, default="./log_{}.json", help="local file path for completion log file (formattable with timestamp)")
        parser.add_argument('--tip-log-remote', metavar='path', type=str, default="/var/lib/jupyter/notebooks/outputs/tip_log.json", help="remote file path for tip log file")
        parser.add_argument('--tip-log-local', metavar='path', type=str, default="./tip_log.json", help="local file path for tip log file")
        parser.add_argument('--protocol-remote', metavar='path', type=str, default="/var/lib/jupyter/notebooks/protocol.py", help="remote file path for protocol file")
        parser.add_argument('--protocol-local', metavar='path', type=str, default="./.tmp_protocol.py", help="local file path for protocol file")
        return cls.reset(**parser.parse_args().__dict__)
