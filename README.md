# localWebServer

## Table of Contents

* [Execute the program](#execute-the-program)
* [Things to do](#things-to-do)

## Execute the program

1. Download from Github the latest version: on **MVP branch** there
is the testing code

2. Open the commander (prompt of the command) in the same directory
of the downloaded repository

3. Install the needed requirements with: `pip install -r requirements.txt`
 and wait the completion
 
4. Run the `app.py` with: `python app.py`

> Pay attention to have the `ot2_ssh_key` and `ot2_ssh_key.pub`
> on the root folder of the repository

### Things to do

- [x] Tested the method of the environment variable for the IP of the robot
- [ ] Add to the environment variable `OT-2-IP` the IP of the robot
- [ ] Test the newer code with the PCR results

In order to include locally on the laptop the IP of the robot:
It can be done with prompt of commands: `setx OT-2-IP <IP-OF-THE-ROBOT>`