from opentrons import protocol_api
import json
import os
import math
from typing import Optional

from opentrons.protocol_api import ProtocolContext
from threading import Thread
import time
import datetime

# For setting and checking the temperature
temp_a = 3.9
temp_check = 4.0
TempUB = temp_check + 0.3


# metadata
metadata = {
    'protocolName': 'Version 1 S9 Station C Technogenetics P20 Multi',
    'author': 'Marco & Giada',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}

NUM_SAMPLES = 96  # start with 8 samples, slowly increase to 48, then 94 (max is 94)
NUM_SEDUTE = 1
TIP_TRACK = True
MM_PER_SAMPLE = 20
SAMPLE_VOL = 20

liquid_headroom = 1.1
mm_tube_capacity = 1450
mm_strips_capacity = 180


def run(ctx: protocol_api.ProtocolContext):
    # Define the Path for the log temperature file
    folder_path = '/var/lib/jupyter/notebooks/outputs'
    temp_file_path = folder_path + '/completion_log.json'
    # FIXME: check this line: without this we can't append the data of the log
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
                # if tempdeck.status != 'holding at target':
                while tempdeck.temperature >= temp_check:
                    print("sleeping for 0.5 s to wait for Temp_Deck")
                    print("current temperature is {}°C".format(tempdeck.temperature))
                    time.sleep(0.5)

                current_Log_dict["status"] = "FAILED"
                current_Log_dict["message"] = "Temperature rose above threshold value"

        Log_Dict["stages"].append(current_Log_dict)
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        with open(temp_file_path, 'w') as outfiletemp:
            json.dump(Log_Dict, outfiletemp)

        print('{}: {}'.format(current_status, message))
    global MM_TYPE

    ctx.comment("Station C Technogenetics protocol for {} samples.".format(NUM_SAMPLES))

    # check source (elution) labware type
    source_plate = ctx.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', '1',
        'chilled elution plate on block from Station B')
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['2', '3', '6', '7', '9']
    ]
    tips20_no_a = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', '11', '20µl tiprack - no tips in row A')
    ]
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '10')]
    tempdeck = ctx.load_module('Temperature Module Gen2', '4')
    pcr_plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul', 'PCR plate')
    mm_strips = ctx.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '8',
        'mastermix strips')
    tempdeck.set_temperature(temp_a)
    tube_block = ctx.load_labware(
        'opentrons_24_aluminumblock_nest_1.5ml_snapcap', '5',
        '2ml screw tube aluminum block for mastermix + controls')

    # pipette
    m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tips20)
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)

    # setup up sample sources and destinations
    num_cols = math.ceil(NUM_SAMPLES / 8)
    sources = source_plate.rows()[0][:num_cols]
    sample_dests = pcr_plate.rows()[0][:num_cols]

    tip_log = {'count': {}}
    tip_file_path = folder_path + '/tip_log.json'
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
                if 'tips20_no_a' in data:
                    tip_log['count']['tips20_no_a'] = data['tips20_no_a']
                else:
                    tip_log['count']['tips20_no_a'] = 0
        else:
            tip_log['count'] = {m20: 0, p300: 0, 'tips20_no_a': 0}
    else:
        tip_log['count'] = {m20: 0, p300: 0, 'tips20_no_a': 0}

    tip_log['tips'] = {
        m20: [tip for rack in tips20 for tip in rack.rows()[0]],
        p300: [tip for rack in tips300 for tip in rack.wells()],
        'tips20_no_a': [tip for rack in tips20_no_a for tip in rack.rows()[0]]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [m20, p300, 'tips20_no_a']
    }

    def pick_up(pip):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip]:
            # print('Replace ' + str(pip.max_volume) + 'µl tipracks before resuming.')
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
        tip_log['count'][pip] += 1
        # print("Picked up {} with {} [#{}]".format(tip_log['tips'][pip][tip_log['count'][pip]-1], pip, tip_log['count'][pip]))

    def pick_up_no_a():
        nonlocal tip_log
        if tip_log['count']['tips20_no_a'] == tip_log['max']['tips20_no_a']:
            ctx.pause('Replace 20ul tiprack in slot 10 (without tips in row A) \
before resuming.')
            tip_log['count']['tips20_no_a'] = 0
        m20.pick_up_tip(tip_log['tips']['tips20_no_a'][tip_log['count']['tips20_no_a']])
        tip_log['count']['tips20_no_a'] += 1
        # print("Picked up {} with {} [#{}]".format(tip_log['tips']['tips20_no_a'][tip_log['count']['tips20_no_a']-1], 'tips20_no_a', tip_log['count']['tips20_no_a']))

    """ mastermix component maps """
    # setup tube mastermix
    num_mm_tubes = math.ceil(MM_PER_SAMPLE * NUM_SAMPLES * liquid_headroom / mm_tube_capacity)
    mm_cols_per_tube = math.ceil(NUM_SAMPLES / num_mm_tubes)
    mm_tube = tube_block.columns()[0][:num_mm_tubes]
    ctx.comment("Mastermix: using {} tubes with at least {:.2f} mL each".format(
        num_mm_tubes, mm_cols_per_tube * MM_PER_SAMPLE * liquid_headroom / 1000))

    # setup strips mastermix
    num_mm_strips = math.ceil(MM_PER_SAMPLE * num_cols * liquid_headroom / mm_strips_capacity)
    mm_cols_per_strips = math.ceil(num_cols / num_mm_strips)
    mm_strip = mm_strips.columns()[:num_mm_strips][0]
    # ctx.comment('Vediamo se stampa quello che vogliamo {}'.format(mm_strip))
    remaining_samples = NUM_SAMPLES * NUM_SEDUTE

    # for _ in range(5):
    #    test_light = BlinkingLight(ctx)
    #    test_light.start()
    #    ctx.delay(30)
    #    test_light.stop()

    # START REPEATED SECTION
    while remaining_samples > 0:
        vol_per_strip_well = min(remaining_samples, 96) / 8 * MM_PER_SAMPLE * 1.1

        # transfer mastermix to strips
        current_status = 'transfer mastermix to strips'
        pick_up(p300)
        for well in mm_strip:
            p300.transfer(vol_per_strip_well, mm_tube, well, new_tip='never')
        p300.drop_tip()

        update_log_file()
        # transfer mastermix to plate
        current_status = 'transfer mastermix to plate'
        pick_up(m20)
        m20.transfer(MM_PER_SAMPLE, mm_strip[0].bottom(0.5), sample_dests,
                     new_tip='never')
        m20.drop_tip()

        update_log_file()

        # transfer samples to corresponding locations
        current_status = 'transfer samples to corresponding locations'
        for i, (s, d) in enumerate(zip(sources, sample_dests)):
            # print(i, end=" ")
            if i == 9:
                pick_up_no_a()
            else:
                pick_up(m20)
            m20.transfer(SAMPLE_VOL, s.bottom(2), d.bottom(2), new_tip='never')
            m20.mix(1, 10, d.bottom(2))
            m20.blow_out(d.top(-2))
            m20.aspirate(5, d.top(2))  # suck in any remaining droplets on way to trash
            m20.drop_tip()
            remaining_samples -= 8

        update_log_file()

        if remaining_samples > 0:
            ctx.home()
            current_status = "remaining samples >0"
            update_log_file()
    # END REPEATED SECTION

    current_status = "finished protocol C"
    # track final used tip
    if TIP_TRACK and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips20': tip_log['count'][m20],
            'tips300': tip_log['count'][p300],
            'tips20_no_a': tip_log['count']['tips20_no_a']
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

    ctx.home()
    update_log_file()


if __name__ == "__main__":
    from opentrons import simulate

    run(simulate.get_protocol_api(metadata["apiLevel"]))
