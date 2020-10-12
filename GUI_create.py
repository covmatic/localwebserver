from scp import SCPClient
import tkinter as tk
from tkinter import simpledialog
import subprocess
import tkinter.filedialog
from tkinter import *
from services import task_runner, protocol_gen
from services.task_runner import OT2_SSH_KEY, OT2_ROBOT_PASSWORD, OT2_REMOTE_LOG_FILEPATH, OT2_TARGET_IP_ADDRESS
import webbrowser
import requests
import time
import app
import os
import signal
from PIL import ImageTk, Image


OPENTRONS_APP = 'C:/Program Files/Opentrons/Opentrons.exe'
# OPENTRONS_APP = 'C:/Users/wassi/AppData/Local/Programs/Opentrons/Opentrons.exe'
WEB_INTERFACE = 'https://ec2-15-161-32-20.eu-south-1.compute.amazonaws.com/stations'

# TODO: Add the List menù to the MAIN GUI.
# Option List for the stations used
OptionList = ["A", "B", "C", "PCR"]

####################################### Classes #######################################################################


class ToggleButton(Frame):
    def __init__(self, master=None, **kwargs):
        Frame.__init__(self, master, **kwargs)

        self.btn = Button(self, text="Lights are OFF", command=self.clicked, bg='red')
        self.btn.grid(column=6, row=4)
        self.lbl = Label(self, text="  Toggle lights: ", bg="white")
        self.lbl.grid(column=5, row=4)

    def clicked(self):
        if self.btn['text'] == "Lights are OFF":
            self.btn.configure(text="Lights are ON", bg='green')
            payload = {'on': True}
            try:
                requests.post("http://" + OT2_TARGET_IP_ADDRESS + ":31950/robot/lights", json=payload).json()
            except ConnectionError:
                pass
        else:
            self.btn.configure(text="Lights are OFF", bg='red')
            payload = {'on': False}
            try:
                requests.post("http://" + OT2_TARGET_IP_ADDRESS + ':31950/robot/lights', json=payload).json()
            except ConnectionError:
                pass

###################################### Functions #######################################################################


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
        subprocess.call(OPENTRONS_APP)
    else:
        tk.messagebox.showinfo('Check', 'You confirm that the machine has already been calibrated')


# def check(butt):
#     lastbarcode = None
#     time.sleep(60)
#     done = False
#     while not done:
#         time.sleep(5)
#         while True:
#             try:
#                 rv = requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/log")
#             except requests.exceptions.ConnectionError:
#                 time.sleep(0.5)
#             else:
#                 break
#         output = rv.json()
#         if output["status"] == "Finished":
#             butt.config(state="enabled")
#             done = True
#             break
#         elif output["status"] == 'Paused':
#             if output['external'] and lastbarcode is None:
#                 last_barcode = simpledialog.askstring(title="User Input",
#                                                       prompt="Please Input Barcode of Exiting Rack:")
#             requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/pause")
#         elif output["external"] and output['status'] != 'Pasued':
#             while last_barcode != simpledialog.askstring(
#                     title="User Input", prompt="Please Input Barcode of Entering Rack:"):
#                 pass
#             last_barcode = None
#             requests.get("http://" + OT2_TARGET_IP_ADDRESS + ":8080/resume")


# It enters also the parameter of the language
def create_protocol(butt, language):

    def ok(frame, sta, sa):
        station = str(sta.get())
        if station != 'PCR':
            try:
                samples = int(sa.get())
                frame.destroy()
                protocol = protocol_gen.protocol_gen(station, num_samples=samples, language=language.get())
                protocol_file = tkinter.filedialog.asksaveasfilename(
                    title="Save Protocol", defaultextension=".py",
                    filetypes=(("python scripts", "*.py"), ("all files", "*.*")))
                if protocol_file is None:
                    return "break"
                else:
                    print('Writing new protocol to {}'.format(protocol_file))
                    with open(protocol_file, 'w') as location:
                        location.write(protocol)
                    print('Uploading protocol to robot...')
                    upload_protocol(protocol_file)
                    print('Done.')
                webbrowser.open(WEB_INTERFACE)  # enter webserver address
            except ValueError:
                tk.messagebox.showinfo('Check', 'Please Input sample Number as Integer to Proceed')
            except FileNotFoundError:
                pass
        else:
            webbrowser.open(WEB_INTERFACE)  # enter webserver address

    # the input dialog
    ap = tk.Tk()
    # ap.geometry('380x110')
    try:
        ap.iconbitmap('./Covmatic_Icon.ico')
    except Exception:
	    pass
    prompt = Label(ap, text='Please choose the desired station ')
    prompt.grid(column=0, row=0)
    station = tk.StringVar(ap)
    station.set(OptionList[0])
    menu = tk.OptionMenu(ap, station, *OptionList)
    menu.config(width=20, font=('Helvetica', 12))
    menu.grid(column=0, row=1)
    prompt1= Label(ap, text='Please number of samples to process ')
    prompt1.grid(column=0, row=2)
    samples = tk.IntVar
    samples= tk.Entry(ap)
    samples.grid(column=0, row=3)
    space = Label(ap, text=' ')
    space.grid(row=4, column=0)
    StartButton = Button(ap, text='Save Protocol and Proceed',
                         command=lambda: ok(ap,station,samples), fg='white', bg='green', width=20)
    StartButton.grid(row=0, column=1)
    quitButton = Button(ap, text='Abort', command=ap.destroy, fg='white',
                        bg='red', width=20)
    quitButton.grid(row=1, column=1)
    OldButton = Button(ap, text='Proceed With Old Protocol',
                       command=lambda: webbrowser.open(WEB_INTERFACE), fg='white', bg='blue', width=20)
    OldButton.grid(row=2, column=1)


def upload_protocol(protocol_file):
    print('Opening ssh connection')
    client = task_runner.create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
    scp_client = SCPClient(client.get_transport())
    print('Uploading protocol file: {}'.format(protocol_file))
    scp_client.put(protocol_file, '/var/lib/jupyter/notebooks/protocol.py')
    scp_client.close()


def shutdown():
    requests.get("http://127.0.0.1:5001/shutdown")
    os.kill(os.getpid(), signal.SIGINT)


def takepicture():
    try:
        requests.post("http://" + OT2_TARGET_IP_ADDRESS + ":31950/camera/picture")
    except ConnectionError:
        pass


def launchgui():
    root = Tk()
    root.title('Local Machine Server')
    try:
        root.iconbitmap('./Covmatic_Icon.ico')
    except Exception:
        pass
    # root.geometry('600x80')
    root.configure(bg='white')
    CalButton = Button(root, text='Calibrate Machine', command=calibrate, fg='black', bg='white', width=60)
    CalButton.grid(row=0, column=0)

    # Adding the switch for the language
    frame = tk.Frame(root)
    language_switch = tk.StringVar(value="ENG")
    lang_frame = frame.grid(row=1, column=1, columnspan=1)
    eng_language = tk.Radiobutton(lang_frame, text="English", variable=language_switch, value="ENG")
    eng_language.grid(row=1, column=1, sticky=tk.W)
    ita_language = tk.Radiobutton(lang_frame, text="Italiano", variable=language_switch, value="ITA")
    ita_language.grid(row=1, column=1, sticky=tk.E)

    ProtButton = Button(root, text='Start New Run', command=lambda: create_protocol(
        ProtButton, language=language_switch), fg='black', bg='white', width=60)
    ProtButton.grid(row=1, column=0)
    KillButton = Button(root, text='Stop Server and Quit', command=shutdown, fg='white',
                        bg='red', width=60)
    KillButton.grid(row=2, column=0)
    # PictureButton = Button(root, text='Capture a picture', command=takepicture, fg='black', bg='purple', width=60)
    # PictureButton.grid(row=2, column=0)
    logo = Image.open("./Covmatic_Logo.png")
    width, height = logo.size
    logo = logo.resize([round(width / 10), round(height / 10)])
    CovmaticLogo = ImageTk.PhotoImage(logo)
    covlabel = Label(image=CovmaticLogo)
    covlabel.grid(row=2, column=1, columnspan=1)
    button = ToggleButton(root)
    button.grid(row=0, column=1)
    root.mainloop()


if __name__ == "__main__":
    try:
        subprocess.Popen([os.sys.executable, './app.py'])
        time.sleep(1.0)
    # subprocess.Popen('cmd.exe /K py ./app.py')
        launchgui()
    except Exception as e:
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
