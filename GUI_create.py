from scp import SCPClient
import tkinter as tk
from tkinter import simpledialog
import subprocess
import tkinter.filedialog
from tkinter import *
from services import task_runner, protocol_gen
from services.task_runner import OT2_SSH_KEY, OT2_ROBOT_PASSWORD, OT2_REMOTE_LOG_FILEPATH,OT2_TARGET_IP_ADDRESS
import webbrowser
import requests
import time
import app


def save_file():
    file = tk.filedialog.asksaveasfilename(title="Save Protocol", defaultextension=".py",
                                           filetypes=(("python scripts", "*.py"), ("all files", "*.*")))
    if file is None:
        return None
    else:
        return file


def calibrate():
    # root = tk.Tk()
    MsgBox = tk.messagebox.askquestion('Calibration', 'Do You want to calibrate this machine?',
                                       icon='warning')
    if MsgBox == 'yes':
        subprocess.call('C:/Users/wassi/AppData/Local/Programs/Opentrons/Opentrons.exe')
    else:
        tk.messagebox.showinfo('Check', 'You confirm that the machine has already been calibrated')


def check(butt):
    lastbarcode = None
    time.sleep(60)
    done = false
    while not done:
        time.sleep(5)
        while True:
            try:
                rv = requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/log")
            except requests.exceptions.ConnectionError:
                time.sleep(0.5)
        else:
            break
        output = rv.json()
        if output["status"] == "Finished":
            butt.config(state="enabled")
            done = True
            break
        elif output["status"] == 'Paused':
            if output['external'] and lastbarcode is None:
                CheckFunction.last_barcode = simpledialog.askstring(title="User Input",
                                                            prompt="Please Input Barcode of Exiting Rack:")
            requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/pause")
        elif output["external"] and output['status'] != 'Pasued':
            while last_barcode != simpledialog.askstring(
                title="User Input", prompt="Please Input Barcode of Entering Rack:"):
                pass
            last_barcode = None
            requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/resume")


def create_protocol(butt):
    # butt.config(state="disabled")
    # ROOT = tk.Tk()
    # ROOT.withdraw()
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
        upload_protocol(protocol_file)
    webbrowser.open('https://ec2-15-161-32-20.eu-south-1.compute.amazonaws.com/stations')  # enter webserver address
    # rdone = False
    # while not rdone:
    #     while True:
    #         try:
    #             rv = requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/log")
    #         except requests.exceptions.ConnectionError:
    #             time.sleep(0.5)
    #         else:
    #             break
    #     output = rv.json()
    #     if output["status"] == "Finished":
    #         butt.config(state="enabled")
    #         rdone = True


def upload_protocol(protocol_file):
    client = task_runner.create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
    scp_client = SCPClient(client.get_transport())
    scp_client.put(protocol_file, '/var/lib/jupyter/notebooks')
    scp_client.close()


def launchgui(F):
    root = Tk()
    root.title('Local Machine Server')
    root.iconbitmap('C:/Users/inse9/OneDrive/Documenti/GitHub/localWebServer/localWebServer/Covmatic_Icon.ico')
    root.geometry('400x50')
    CalButton = Button(root, text='Calibrate Machine', command=calibrate, fg='black', bg='white', width=60)
    CalButton.grid(row=0, column=0)
    ProtButton = Button(root, text='Start New Run', command=lambda: create_protocol(ProtButton), fg='black',
                        bg='white', width=60)
    ProtButton.grid(row=1, column=0)
    KillButton = Button(root, text='Stop Server', command=lambda: F.terminate, fg='black',
                        bg='white', width=60)
    KillButton.grid(row=2, column=0)
    root.mainloop()


if __name__ == "__main__":
    # cmd = subprocess.Popen('cmd.exe /K cd C:/Users/wassi/Desktop/localwebserver')
    F = subprocess.Popen('cmd.exe /K py ./app.py')
    launchgui(F)

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