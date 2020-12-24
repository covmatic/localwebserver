from .utils import SingletonMeta, FunctionCaseStartWith
import configargparse
import argparse
import os


desktop_file = FunctionCaseStartWith(os.sys.platform)
tempdeck_desktop_file = FunctionCaseStartWith(os.sys.platform)


@desktop_file.case('linux')
def desktop_file_linux():
    return os.path.expanduser("~/.local/share/applications/covmatic.desktop")


@desktop_file.case(('win32', 'cygwin'))
def desktop_file_win():
    import winshell
    return os.path.join(winshell.desktop(), "Covmatic LocalWebServer.lnk")


@desktop_file.case('')  # all other
def desktop_file_other():
    return ""


@tempdeck_desktop_file.case('linux')
def tempdeck_desktop_file_linux():
    return os.path.expanduser("~/.local/share/applications/covmatic_tempdeck.desktop")


@tempdeck_desktop_file.case(('win32', 'cygwin'))
def tempdeck_desktop_file_win():
    import winshell
    return os.path.join(winshell.desktop(), "Covmatic TempDeck.lnk")


@tempdeck_desktop_file.case('')  # all other
def tempdeck_desktop_file_other():
    return ""


class Args(argparse.Namespace, metaclass=SingletonMeta):
    @classmethod
    def parse(cls, description):
        parser = configargparse.ArgParser(description=description, default_config_files=[os.path.join(os.path.expanduser(d), "covmatic.conf") for d in ("~", ".")])
        parser.add_argument('-I', '--ip', metavar='address', type=str, required=False, help="the robot's IP address or hostname")
        parser.add_argument('-A', '--app', metavar='path', type=str, default="C:/Program Files/Opentrons/Opentrons.exe", help="the Opentrons App filepath")
        parser.add_argument('-S', '--station', metavar='name', type=str, default="A", help="the default station type")
        parser.add_argument('-L', '--lang', metavar='lang', type=str, default="ENG", help="the default message language")
        parser.add_argument('-K', '--ssh-key', metavar='file', type=str, default=os.path.expanduser("~/ot2_ssh_key"), help="SSH key file path")
        parser.add_argument('-P', '--pwd', metavar='pwd', type=str, default="", help="the SSH key passphrase")
        parser.add_argument('-U', '--user', metavar='name', type=str, default="root", help="the SSH username")
        parser.add_argument('--barcode-port', metavar='port', type=int, default=5002, help="the barcode server port")
        parser.add_argument('--no-wait-log', dest="wait_log", action='store_false', help='make the protocol start as soon as possible, without waiting for the first log request')
        parser.add_argument('--pcr-app', metavar="path", type=str, default="C:/PCR_BioRad/APIs/BioRad_CFX_API_v1.4/BioRad.Example_Application.exe", help="the PCR app filepath")
        parser.add_argument('--pcr-results', metavar="path", type=str, default="C:/PCR_BioRad/json_results/????????_Data_??-??-????_??-??-??_Result.json", help="the PCR results filepath (scheme)")
        parser.add_argument('--pcr-pcrd', metavar="path", type=str, default="C:/PCR_BioRad/pcrd_results", help="the PCR pcrd folder")
        parser.add_argument('--web-app-fixed', metavar='url', type=str, default="", help="the Web App URL to be opened independently without building path with the station name")
        parser.add_argument('--web-app', metavar='url', type=str, default="", help="the Web App URL")
        parser.add_argument('--log-local', metavar='path', type=str, default="", help="local file path for run log file")
        parser.add_argument('--tip-log-remote', metavar='path', type=str, default="/var/lib/jupyter/notebooks/outputs/tip_log.json", help="remote file path for tip log file")
        parser.add_argument('--tip-log-local', metavar='path', type=str, default=os.path.join(os.path.dirname(__file__), "tip_log.json"), help="local file path for tip log file")
        parser.add_argument('--copan48-json-remote', metavar='path', type=str, default="", help="remote file path for copan48 configuration (this is used for rack configuration)")
        parser.add_argument('--copan48-json-local', metavar='path', type=str, default="", help="local file path for copan48 configuration (if both remote and local paths are given, this is used for rack configuration)")
        parser.add_argument('--magnet-json-remote', metavar='path', type=str, default="", help="remote file path for magnet configuration (this is used for magnet configuration)")
        parser.add_argument('--magnet-json-local', metavar='path', type=str, default="", help="local file path for magnet configuration (if both remote and local paths are given, this is used for magnet configuration)")
        parser.add_argument('--start-at', action='store_true', help='enable the start_at protocol argument in the upload protocol window')
        parser.add_argument('--protocol-remote', metavar='path', type=str, default="/var/lib/jupyter/notebooks/protocol.py", help="remote file path for protocol file")
        parser.add_argument('--protocol-local', metavar='path', type=str, default=os.path.join(os.path.dirname(__file__), ".tmp_protocol.py"), help="local file path for protocol file")
        parser.add_argument('--api-prefix', metavar='prefix', type=str, default="/api", help="the prefix for localwebserver API paths")
        parser.add_argument('--pcr-backup', metavar='path', type=str, default=os.path.expanduser("~/.pcr_backup"), help="the backup folder for PCR result files")
        parser.add_argument('--desktop-file', metavar='path', type=str, default=desktop_file(), help="(setup) the desktop file path for the GUI")
        parser.add_argument('--tempdeck-desktop-file', metavar='path', type=str, default=tempdeck_desktop_file(), help="(setup) the desktop file path for the Tempdeck GUI")
        parser.add_argument('--tempdeck-desktop', action='store_true', help='(setup) create a desktop file for the Tempdeck GUI')
        parser.add_argument('--python', metavar='path', type=str, default=os.sys.executable, help="(setup) the Python instance file path")
        return cls.reset(**parser.parse_known_args()[0].__dict__)
    
    @classmethod
    def pull(cls, description):
        if not cls().__dict__:
            cls.parse(description)
        return cls()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
