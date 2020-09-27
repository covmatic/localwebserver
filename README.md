# localWebServer

In this "documentation" should be explained some part of the code and how to set
this program for the first time.
## Table of Contents

* [Execute the program](#execute-the-program)
* [Things to do](#things-to-do)
* [IT Technicians instructions](#instruction-for-it-technicians)
    * [Task Runner](#task-runner)
    * [api_protocol_automation](#api-protocol-automation)
    * [Troubleshooting](#troubleshooting)
## Execute the program

1. Download from Github the latest version: on **MVP branch** there
is the testing code

2. Open the commander (prompt of the command) in the same directory
of the downloaded repository

3. Assign the IP or the localhost name of the robot to the environment variable
called `OT-2-IP` 

4. Install the needed requirements with: `pip install -r requirements.txt`
 and wait the completion
 
5. Run the [`app.py`](app.py) with: `python app.py`

> If you want to avoid to the passage 4, write a .bat file with inside
> `python app.py`

> Pay attention to have the `ot2_ssh_key` and `ot2_ssh_key.pub`
> on the root folder of the repository

### Things to do

- [x] Tested the method of the environment variable for the IP of the robot
- [ ] Add to the environment variable `OT-2-IP` the IP/Hostname of the robot
- [x] Test the newer code with the PCR results
- [x] Added the resources for Pause and Resume
- [ ] Tested Pause and Resume on the real system
- [ ] Check the newer protocols
- [ ] Update the [`task_runner.py`](/services/task_runner.py)
- [ ] Update the interface to the newest MBR
- [ ] Testing
- [ ] Clean the repository and the code

In order to include locally on the laptop the Hostname of the robot:
It can be done with prompt of commands:

`setx OT-2-IP <HOSTNAME-OF-THE-ROBOT>`

### Instruction for IT technicians

#### Task runner
The core of the program is contained inside [`task_runner.py`](services/task_runner.py)
In that program there is a structure if-elif-else which covers all the situations
involved for the execution of the protocols.
For example:
```python
try:
    station = protocol.station
    action = protocol.action
    if action == "settemp":
        print("station 1 is setting the temperature module!")
        ###################################################################################
        client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
        # client = create_ssh_client(usr='root', key_file=key, pwd=target_machine_password)
        channel = client.invoke_shell()
        channel.send('opentrons_execute {}/{} -n \n'.format(OT2_PROTOCOL_PATH, OT2_TEMP_PROTOCOL_FILE))
        channel.send('exit \n')
        code = channel.recv_exit_status()
        print("I got the code: {}".format(code))
        local_filepath = ssh_scp()

```

The variable: `station = protocol.station` is the object which represents the station,
instead: `action = protocol.action` is the object which relate the action, so the endpoint
related to the particular protocol to execute.
These 2 objects are used for defining what is "read" by the web interface.
In this example you have that if the action is `settemp` (whatever is the station)
it executes the following: 
* Access to the machine as root with ssh
* Invoke a shell inside the machine
* Execute the protocols with the name stored in the variable `OT2_TEMP_PROTOCOL_FILE`
* Exit from the ssh and printed the exit code
* Copied in the root folder the log of the machine generated in the protocol

> Important: If everything is good in the machine the error code is 0. 
>
> E.g: `I got the code: 0`

#### api protocol automation

The module [`api_protocol_automation.py`](api/api_protocol_automation.py) it's another interesting
program for working on the Opentrons side.
Particularly inside the **<ins>class</ins>** `CheckFunction`
there is this piece of code which shows the piece of the process in which the machine is arrived.

```python
client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
scp_client = SCPClient(client.get_transport())
logging_file = 'completion_log'
scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=logging_file)
scp_client.close()
# Searching all logfile results file
result_file = glob.glob('./' + logging_file)
# Sorting the PCR's results
result_file.sort(key=os.path.getctime)
if result_file:
    with open('./' + logging_file, 'r') as r:
        status = json.load(r)
    if status["stages"][-1]["status"] == "Progress":
        output = status["stages"][-1]["stage_name"]
    else:
        output = "Starting Protocol"
else:
    output = "initializing"

return {"status": False, "res": output}, 200
```

The code do the following:

* Create a connection to the robot and get the current log
* Searching all the files in the root folder called as `logging_file`
* Sorting by creation time
* Open that file and read the last one which the status is progress
* If the log file hasn't status in Progress is at the beginning
* If the log file isn't existing, it is initializing
* the output is returned, note: 200 is the HTTP code: it means everything is fine.

#### Troubleshooting:

The main object to observe for doing troubleshooting is using the shell
after executing the program. 

1. If the robot doesn't move/no noises when you are executing the protocols:

    In this case probably you are seeing on the shell something like: Windows Error - Not connected.
    Solution: Check the `OT-2-IP` if it corrisponds to the hostname of the robot and it
    is reachable by IP address.

2. If there is shown on the interface or on the shell the code: `403 FORBIDDEN`:

    It happens when the previous run for some reason was failed.
    
    Solution: STOP the localwebserver application, Delete the file `app.db` in the [store](store) folder
    If you want to be sure, you can delete it each morning.

3. If the execution of the protocol didn't work and/or is shown a code different from: `I got code: 0`
 
    Generally is something related to the protocol execution: errors in the protocol,
     missing some custom labware loading.
    Solution: Try to execute that protocol from the ssh connection manually, look at the error and fix.

> We didn't found any critical error, if everything was perfectly setted we didn't get any errors
>or strange bugs.

![Tux, the Linux mascot](https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Classic_flat_look_3D.svg/155px-Classic_flat_look_3D.svg.png)