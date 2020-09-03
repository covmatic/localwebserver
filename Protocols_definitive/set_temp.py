from opentrons import protocol_api
from opentrons.drivers.rpi_drivers import gpio
import json
import os
import datetime
import time

# metadata
metadata = {
    'protocolName': 'Version 1 Set/Check_Temp',
    'author': 'Fede Wassim and German',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}

temp_a = 3.9
temp_check = 4.0
TempUB = temp_check + 0.3


def run(ctx: protocol_api.ProtocolContext):
    # Define the Path for the log temperature file
    folder_path = '/var/lib/jupyter/notebooks/outputs'
    temp_file_path = folder_path + '/completion_log.json'
    Log_Dict = {"stages": []}  # For log file data
    current_status = "Setting Temperature"

    def update_log_file(status="SUCCESS", check_temperature=True, message=None):
        current_Log_dict = {"stage_name": current_status,
                            "time": datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S:%f"),
                            "temp": None,
                            "status": status,
                            "message": None}
        if check_temperature:
            current_Log_dict["temp"] = tempdeck.temperature
            if tempdeck.temperature >= TempUB and tempdeck.status != 'holding at target':
                if tempdeck.status != 'holding at target':
                    ctx.pause('The temperature is above {}°C'.format(TempUB))
                    while tempdeck.temperature >= temp_check:
                        print("sleeping for 0.5 s to wait for Temp_Deck")
                        print("current temperature is {}°C".format(tempdeck.temperature))
                        time.sleep(0.1)

                    current_Log_dict["status"] = "FAILED"
                    current_Log_dict["message"] = "Temperature rose above threshold value"
        Log_Dict["stages"].append(current_Log_dict)
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        with open(temp_file_path, 'w') as outfiletemp:
            json.dump(Log_Dict, outfiletemp)

        print('{}: {}'.format(current_status, message))


    global MM_TYPE

    try:
        tempdeck = ctx.load_module('Temperature Module Gen2', '4')
        tempdeck.set_temperature(temp_a)  # it sets the temp to 4°C
        print(tempdeck.temperature)
        update_log_file()

    except RuntimeError:
        update_log_file(message='Temperature module is disconnected', check_temperature=False)
