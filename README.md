# LocalWebServer
This software is part of the *Covmatic* project.  
Visit the website https://covmatic.org/ for more documentation and information.

## Table of Contents
* [Installation](#installation)
* [Setup](#setup)
* [Execution](#execution)
* [LocalWebServer](#localwebserver-gui)
* [TempDeck](#tempdeck-gui)

## Installation
You can [install the Covmatic LocalWebServer via `pip`](https://pypi.org/project/covmatic-localwebserver):
```
<python> -m pip install covmatic-localwebserver
```
Where `<python>` should be changed for the Python instance you wish to install the LocalWebServer onto. We will be following this convention for all the next instructions. 

### Troubleshooting
In some cases, the `opentrons` package fails to install as a dependency of this package.
If it happens, please install the `opentrons` package separately.
```
<python> -m pip install opentrons
<python> -m pip install covmatic-localwebserver
```
## Setup
To set up the LocalWebServer application, run
```
<python> -m covmatic_lws.setup
``` 
This will create a desktop link and open in a text editor the file `covmatic.conf` in your user home directory.
To create a link also for the TempDeck GUI, please run
```
<python> -m covmatic_lws.setup --tempdeck-desktop
``` 
This functionality is supported in Windows and Linux.

If you are running another OS, please open the `covmatic.conf` file manually.
If you would like an automatic desktop link creator for your OS, please open an issue on GitHub. 

### Configuration
The file `covmatic.conf` stores configuration settings for running the LocalWebServer. The most important settings are
 - `ip`: the ip address or hostname of the Opentrons robot you want to connect to
 - `ssh-key`: SSH key file path (default is `~/ot2_ssh_key`). Please, make sure you have the correct SSH key file in the specified path
 - `pwd`: the passphrase for the SSH key used when connecting to the Opentrons robot
 - `web-app`: the webapp url (including, eventually, `https://`) that is concatenated with the station name retrieved from the robot
 - `web-app-fixed`: the url (including, eventually, `https://`) that will not be concatenated with the retrieved station name
To learn how to set up SSH on your Opentrons robot, please refer to [the official guide](https://support.opentrons.com/en/articles/3203681-setting-up-ssh-access-to-your-ot-2).

An example configuration file would be
```
ip=robot-name.local
pwd=pass
web-app=https://covmatic-web-app.com
```

Other useful settings are:
 - `app`: the Opentrons App filepath (default is `C:/Program Files/Opentrons/Opentrons.exe`)
 - `station`: the name of the default station protocol (default is `A`)
 - `lang`: the default message language (default is `ENG`)

For a complete list of settings, run
```
<python> -m covmatic_lws -h
```

## Execution
To start the Covmatic LocalWebServer gui, run
```
<python> -m covmatic_lws.gui
```
To start the Covmatic TempDeck gui, run
```
<python> -m covmatic_lws.gui.tempdeck
```
If you ran the setup program, you will have desktop entries for these applications

### Linux
 - The `Covmatic` app (blue icon) is the LocalWebServer GUI
 - The `TempDeck` app (red icon) is the TempDeck GUI

### Windows
 - The `Covmatic Localwebser` link (blue icon) is the LocalWebServer GUI
 - The `Covmatic TempDeck` link (red icon) is the TempDeck GUI

## LocalWebServer GUI
The LocalWebServer GUI has a main window where you can see
 - The Covmatic logo
 - The robot ip/hostname
 - Two columns of buttons

Please, check that the ip/hostname corresponds to the robot you want to connect to.
If the robot is offline, `(disconnected)` will show under the robot's ip/hostname.

In the first column you will find buttons for functions strictly related to robot
 - Package version button.
 This button shows the current version of the [protocol package](https://github.com/covmatic/stations) installed on the robot.
 It should read `Stations <version>`.
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
- Run Log button. This button opens (or closes) the run log window.
  The run log window displays the protocol run log in real time. It is reset at the start of a new run.

In the second column you will find buttons related to services external to the robot
- Opentrons button. This button launches the Opentrons app.
  You will need this app for calibration procedures.
  If the app doesn't open, please check that the app's path matches the path specified in the [configuration file](#configuration)
- LocalWebServer button. This button allows for turning on and off the local web server.
  If the button is blue, the server is on. 
  If the button is white, the server is off.
  By clicking the button, you can toggle the server state.
- WebApp button. This button opens the web app in a web browser.
  If the [`web-app` setting](#configuration) is unset, this button is disabled.

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

## TempDeck GUI
This GUI allows you to control multiple Opentrons Temperature modules (the *TempDeck*) connected via USB to your laptop.
You can find more information about it [here](https://support.opentrons.com/en/articles/1820119-temperature-module).

There is an entry field where you can specify the target temperature.
There are 3 buttons
- Refresh button. Rescan the USB ports to update the list of connected TempDecks.
- Set button. Set the temperature of all connected TempDecks to the specified temperature.
- Deactivate button. Deactivate all connected TempDeks.


<!---
Copyright (c) 2020 Covmatic.
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-->
