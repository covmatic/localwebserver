# localWebServer

In this "documentation" should be explained some part of the code and how to set
this program for the first time.

The full documentation and informations can be obtained from: https://covmatic.org/

Consult our [wiki](https://github.com/OpenSourceCovidTesting/localWebServer/wiki) for setting the program

## Table of Contents

* [Setup](#setup)
* [Execute the program](#execute-the-program)
  * [Overview](#overview)
* [Things to do](#things-to-do)
* [Troubleshooting](#troubleshooting)
* [Licence](#licence)

## Setup

1. Download from Github the latest version: on **MVP branch** there
is the testing code

2. Go your user home directory. Usually it is
   - `C:/Users/<user>` on Windows
   - `/home/<user>` on Linux

   Create a file named `covmatic.conf`. In this file you can specify custom settings. Required settings are
   - `ip`: the ip address or hostname of the Opentrons robot you want to connext to
   - `pwd`: the passphrase for the SSH key used when connecting to the Opentrons robot
   
   Other useful settings are:
   - `ssh-key`: SSH key file path (default is `./ot2_ssh_key`). Please, make sure you have the correct SSH key file in the specified path. If you get authentication errors, this is the setting you want to check first.
   - `path`: the Opentrons App filepath (default is `C:/Program Files/Opentrons/Opentrons.exe`)
   - `station name`: the name of the default station protocol (default is `A`)
   - `lang`: the default message language (default is `ENG`)
   
   For a complete list of settings, go to the `localWebServer` directory and execute in a terminal:
   ```
   python -m gui -h
   ```

3. Install the needed requirements. Go to the `localWebServer` directory and execute in a terminal:
   ```
   python -m pip install -r requirements.txt
   ```
   This step will download files from the internet and it may take a couple of minutes.
 
## Execute the program
Run the [`gui`](gui). You can do one of the following
  - Go to the `localWebServer` directory and execute in a terminal:
  
    ```
    python -m gui
    ```
  - On Windows, double click on [`LocalWebServer.bat`](LocalWebServer.bat)

### Overview
The GUI has a main window where you can see
 - The Covmatic logo
 - The robot ip/hostname
 - Two columns of buttons
Please, check that the ip/hostname corresponds to the robot you want to connect to.
If the robot is offline, the GUI exits with a RuntimeError (`Cannot connect to <ip/hostname>`)

In the first column you will find buttons for functions strictly related to robot
 - Package version button.
 This button shows the current version of the protocol package installed on the robot.
 It should read `System9 <version>`.
If the button is blue, the package is up to date.
If the button is white, the package is outdated: by clicking the button, you can update the package to the latest version (this may take a minute).
The button should then turn blue, displaying the updated version number.
- Robot lights button. This button allows for turning on and off the robot rail lights.
If the button is blue, the lights are on. 
If the button is white, the lights are off.
By clicking the button, you can toggle the lights.
- Home button. This button sends the robot deck home. Please, don't use this button when a protocol is running, as it may crash the process.
- Protocol upload button. This button opens (or closes) the *Protocol upload* window.
- Jupyter button. This buttons opens the robot's Jupyter server in a web browser.

In the second column you will find buttons related to services external to the robot
- Opentrons button. This button launches the Opentrons app.
  You will need this app for calibration procedures.
  If the app doesn't open, please check that the app's path matches the path specified in the [configuration file](#setup)
- LocalWebServer button. This button allows for turning on and off the local web server.
  If the button is blue, the server is on. 
  If the button is white, the server is off.
  By clicking the button, you can toggle the server state.
- WebApp button. This button opens the web app in a web browser.

#### Protocol upload
The protocol upload window allows you to specify protocol parameters and upload the generated protocol file to the robot.
 - Station menu. This menu allows you to specify which station protocol to use. The default choice is regulated by the [`station` setting](#setup)
 - Number of samples entry. This entry field allows you to specify the number of samples that you want to process in your protocol
 - Next tips. Here you can see which tip locations will be the next to be picked by the robot (for each type of tip rack).
 - Save button. Save protocol file to a custom path.
 - Upload button. Upload file to the robot. If this is not clicked, no changes are made to the robot's protocol.
 - Language menu. This menu allows you to choose the message language. The default choice is regulated by the [`lang` setting](#setup)
 - Reset tips button. This button resets the tip log. The robot will start picking tips from the first position of each rack.
   This button has immediate effect on the robot.


## Things to do

- [x] Configuration file support for settings
- [x] Test the newer code with the PCR results
- [x] Added the resources for Pause and Resume
- [x] Tested Pause and Resume on the real system
- [x] Check the newer protocols
- [ ] Troubleshooting section
- [ ] Update the wiki page
- [ ] Update the [`task_runner.py`](/services/task_runner.py)
- [ ] Update the interface to the newest MBR
- [ ] Testing
- [ ] Clean the repository and the code


## Special Thanks

I want to thank to each one that helped and collaborate to realize this project!
This was possible thanks to the help of each volunteer and to the ideas of everyone,
the hard work in the lab, the programming and maintaining of the code.

Thank you and Congrats to all!

Here you can find us: https://covmatic.org/about-us/

## Licence
Copyright (c) 2020 Covmatic.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 


![Tux, the Linux mascot](https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Classic_flat_look_3D.svg/155px-Classic_flat_look_3D.svg.png)
