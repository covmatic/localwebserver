from opentrons import protocol_api
import json
import os
import math
import datetime
import time

# metadata
metadata = {
    'protocolName': 'Version 1 S9 Station C BP PrimerDesign P20 Multi',
    'author': 'Fede Wassim and German',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}

NUM_SAMPLES = 16  # start with 8 samples, slowly increase to 48, then 94 (max is 94)
PREPARE_MASTERMIX = True
TIP_TRACK = True  # i want to keep track of tips
LOG = True
temp_a = 22.9
temp_check = 23.0
TempUB = temp_check + 1.0


def run(ctx: protocol_api.ProtocolContext):
    # Define the Path for the logs
    folder_path = '/var/lib/jupyter/notebooks/outputs'
    temp_file_path = folder_path + '/completion_log.json'
    Log_Dict = {"stages": []}  # For log file data
    current_status = "Setting environment"

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

                    # tempdeck.await_temperature(temp_check)  # not sure if needed or we break the protocol
                    ctx.resume()
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
        # check source (elution) labware type
        source_plate = ctx.load_labware(
            'opentrons_96_aluminumblock_nest_wellplate_100ul', '1',
            'chilled elution plate on block from Station B')
        tips20 = [
            ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
            for slot in ['3', '6', '8', '9', '10', '11']
        ]
        tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '2')]
        tempdeck = ctx.load_module('Temperature Module Gen2', '4')
        pcr_plate = tempdeck.load_labware(
            'opentrons_96_aluminumblock_biorad_wellplate_200ul', 'PCR plate')  # this is the newer pcr wells plate
        mm_strips = ctx.load_labware(
            'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '7',
            'mastermix strips')
        tempdeck.set_temperature(temp_a)  # it sets the temp to 4°C
        # my modification
        tube_block = ctx.load_labware(
            'opentrons_24_aluminumblock_nest_1.5ml_snapcap', '5',
            '2ml screw tube aluminum block for mastermix + controls')
        print(tempdeck.temperature)

        # pipette
        m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tips20)
        p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)

        update_log_file()

        # setup up sample sources and destinations
        num_cols = math.ceil(NUM_SAMPLES / 8)
        sources = source_plate.rows()[0][:num_cols]
        sample_dests = pcr_plate.rows()[0][:num_cols]

        """Read the number of the tips from the json file if previously is runned the code.
        If the file doesn't exist it creates a new one. If it exists it reads the number of tips used."""

        tip_log = {'count': {}}
        tip_file_path = folder_path + '/tip_log.json'
        # if i need to simulate and check the json file i need to remove the not
        if TIP_TRACK and not ctx.is_simulating():
            if os.path.isfile(tip_file_path):
                with open(tip_file_path) as json_file:
                    data = json.load(json_file)
                    if 'tips20' in data:
                        tip_log['count'][m20] = data['tips20']
                    else:
                        tip_log['count'][m20] = 0
                    if 'tips300' in data:
                        tip_log['count'][p300] = data['tips300']
                    else:
                        tip_log['count'][p300] = 0
            else:
                tip_log['count'] = {m20: 0, p300: 0}
        else:
            tip_log['count'] = {m20: 0, p300: 0}

            """now it counts the tips: tip is the variable of the list
                 that actually is written and is taken by each rack in
                tips20/tips300 for tips20 are considered the tips
                 in the first row of the rack."""

        tip_log['tips'] = {
            m20: [tip for rack in tips20 for tip in rack.rows()[0]],
            p300: [tip for rack in tips300 for tip in rack.wells()]
        }
        tip_log['max'] = {
            pip: len(tip_log['tips'][pip])
            for pip in [m20, p300]
        }

        def pick_up(pip):
            nonlocal tip_log
            if tip_log['count'][pip] == tip_log['max'][pip]:
                ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
    resuming.')
                pip.reset_tipracks()
                tip_log['count'][pip] = 0
            pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
            tip_log['count'][pip] += 1

        """ mastermix component maps """
        mm_tube = tube_block.wells()[0]
        mm_dict = {
            'volume': 12,
            'components': {
                tube: vol
                for tube, vol in zip(tube_block.columns()[1], [10, 2])
            }
        }

        if PREPARE_MASTERMIX:

            current_status = "Preparing Mastermix"

            vol_overage = 1.2  # decrease overage for small sample number

            for i, (tube, vol) in enumerate(mm_dict['components'].items()):
                comp_vol = vol * NUM_SAMPLES * vol_overage
                pick_up(p300)
                num_trans = math.ceil(comp_vol / 160)
                vol_per_trans = comp_vol / num_trans
                for _ in range(num_trans):
                    p300.air_gap(20)
                    p300.aspirate(vol_per_trans, tube)
                    ctx.delay(seconds=3)
                    p300.touch_tip(tube)
                    p300.air_gap(20)
                    p300.dispense(20, mm_tube.top())  # void air gap
                    p300.dispense(vol_per_trans, mm_tube.bottom(2))
                    p300.dispense(20, mm_tube.top())  # void pre-loaded air gap
                    p300.blow_out(mm_tube.top())
                    p300.touch_tip(mm_tube)
                if i < len(mm_dict['components'].items()) - 1:  # only keep tip if last component and p300 in use
                    p300.drop_tip()
            mm_total_vol = mm_dict['volume'] * NUM_SAMPLES * vol_overage
            if not p300.hw_pipette['has_tip']:  # pickup tip with P300 if necessary for mixing
                pick_up(p300)
            mix_vol = mm_total_vol / 2 if mm_total_vol / 2 <= 200 else 200  # mix volume is 1/2 MM total, maxing at 200µl
            mix_loc = mm_tube.bottom(20) if NUM_SAMPLES > 48 else mm_tube.bottom(5)
            p300.mix(7, mix_vol, mix_loc)
            p300.blow_out(mm_tube.top())
            p300.touch_tip()

            update_log_file()

        # transfer mastermix to strips
        current_status = "Transfering mastermix to strips"
        vol_per_strip_well = num_cols * mm_dict['volume'] * 1.1
        mm_strip = mm_strips.columns()[0]
        if not p300.hw_pipette['has_tip']:
            pick_up(p300)
        for well in mm_strip:
            p300.transfer(vol_per_strip_well, mm_tube, well, new_tip='never')
        update_log_file()

        # transfer mastermix to plate
        current_status = "Transfering mastermix to plate"
        mm_vol = mm_dict['volume']
        pick_up(m20)
        m20.transfer(mm_vol, mm_strip[0].bottom(0.5), sample_dests,
                     new_tip='never')
        m20.drop_tip()
        update_log_file()

        # transfer samples to corresponding locations
        current_status = "Transfering mastermix to plate"
        sample_vol = 20 - mm_vol
        for s, d in zip(sources, sample_dests):
            pick_up(m20)
            m20.transfer(sample_vol, s.bottom(2), d.bottom(2), new_tip='never')
            m20.mix(1, 10, d.bottom(2))
            m20.blow_out(d.top(-2))
            m20.aspirate(5, d.top(2))  # suck in any remaining droplets on way to trash
            m20.drop_tip()

        update_log_file()

        current_status = "Finished"
        ctx.home()
        update_log_file()

        # track final used tip
        if TIP_TRACK and not ctx.is_simulating():  # i have putted the not as the original
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
            data = {
                'tips20': tip_log['count'][m20],
                'tips300': tip_log['count'][p300]
            }
            with open(tip_file_path, 'w') as outfile:
                json.dump(data, outfile)

    except RuntimeError:
        update_log_file(status='FAILED', check_temperature=False, message = "RUNTIME ERROR")
