from datetime import datetime

from scp import SCPClient
import tkinter as tk
import tkinter.filedialog
from tkinter import simpledialog
from tkinter import messagebox
from api import api
from database import init_db
from flask import Flask
from flask_cors import CORS
from services import task_runner, protocol_gen
from services.task_runner import OT2_SSH_KEY, OT2_ROBOT_PASSWORD, OT2_REMOTE_LOG_FILEPATH
from views import bp_automation
import subprocess


def create_app():
    app = Flask(__name__)
    app.secret_key = b'_5#y2L"s8zxec]/'
    app.config.from_object('config')

    # Init all plugins
    CORS(app)
    init_db(app)
    api.init_app(app)

    # Register all views blueprints
    app.register_blueprint(bp_automation)
    return app


def save_file():
    file = tk.filedialog.asksaveasfilename(title="Save Protocol", defaultextension=".py",
                                       filetypes=(("python scripts", "*.py"), ("all files", "*.*")))
    if file is None:
        return None
    else:
        return file


def calibrate():
    MsgBox = tk.messagebox.askquestion('Calibration', 'Do You want to calibrate this machine?',
                                    icon='warning')
    if MsgBox == 'yes':
        subprocess.call('C:/Users/wassi/AppData/Local/Programs/Opentrons/Opentrons.exe')
    else:
        tk.messagebox.showinfo('Check', 'You confirm that the machine has already been calibrated')


def calibrate_message():
    root = tk.Tk()
    canvas1 = tk.Canvas(root, width=200, height=100)
    canvas1.pack()
    button1 = tk.Button(root, text='Calibrate Machine', command=calibrate(), bg='brown', fg='white')

def create_protocol():
    ROOT = tk.Tk()
    ROOT.withdraw()
    # the input dialog
    correct_input = False
    station = simpledialog.askstring(title="User Input",
                                     prompt="Please Input Station Name:")
    while not correct_input:
        if station in protocol_gen._classes.keys():
            correct_input = True
        elif station is None:
            pass
        else:
            station = simpledialog.askstring(title="User Input",
                                             prompt="Please Enter A Valid Input Station Name:")
    samples = simpledialog.askinteger(title="User Input",
                                      prompt="Please Input Number of Samples:")
    if station != 'PCR':
        protocol = protocol_gen.protocol_gen(station, num_samples=samples)
        protocol_file = save_file()
        with open(protocol_file, 'w') as location:
            location.write(protocol)
        #upload_protocol(protocol_file)
    calibrate()


def upload_protocol(protocol_file):
    client = task_runner.create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
    scp_client = SCPClient(client.get_transport())
    scp_client.put(protocol_file, '/var/lib/jupyter/notebooks')
    scp_client.close()


if __name__ == "__main__":
    local_app = create_app()
    task_runner.start_scheduler(local_app)
    create_protocol()
    local_app.run(host='127.0.0.1', port=5001, debug=False)


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
