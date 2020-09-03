from opentrons import protocol_api
import json
import os
import math
import time
import datetime

# metadata
metadata = {
    'protocolName': 'Version 1 Station A Technogenetics',
    'author': 'Marco & Giada',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}

NUM_SAMPLES = 8
SAMPLE_VOLUME = 200
LYSIS_VOLUME = 400
PK_VOLUME = 30
BEADS_VOLUME = 10
TIP_TRACK = True

DEFAULT_ASPIRATE = 100
DEFAULT_DISPENSE = 100

LYSIS_RATE_ASPIRATE = 100
LYSIS_RATE_DISPENSE = 100

liquid_headroom = 1.1
pk_capacity = 180

# For setting and checking the temperature
temp_a = 24.9
temp_check = 25.0
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

    ctx.comment("Station A Technogenetics protocol for {} COPAN 330C samples.".format(NUM_SAMPLES))

    current_status = 'load labware'
    # load labware
    source_racks = [ctx.load_labware(
        'copan_15_tuberack_14000ul', slot, 'source tuberack ' + str(i + 1))
        for i, slot in enumerate(['2', '3', '5', '6'])]
    dest_plate = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', '1', '96-deepwell sample plate')
    tempdeck = ctx.load_module('Temperature Module Gen2', '10')

    strips_block = tempdeck.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
        'chilled tubeblock for proteinase K (first 3 strips) and beads (strip 12)')
    beads = strips_block.rows()[0][11]

    lys_buff = ctx.load_labware(
        'opentrons_6_tuberack_falcon_50ml_conical', '4',
        '50ml tuberack for lysis buffer + PK (tube A1)').wells()[0]
    tipracks1000 = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot,
                                     '1000µl filter tiprack')
                    for slot in ['8', '9', '11']]
    tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '7',
                                   '20µl filter tiprack')]

    # load pipette
    m20 = ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=tipracks20)
    p1000 = ctx.load_instrument(
        'p1000_single_gen2', 'right', tip_racks=tipracks1000)
    p1000.flow_rate.aspirate = DEFAULT_ASPIRATE
    p1000.flow_rate.dispense = DEFAULT_DISPENSE
    p1000.flow_rate.blow_out = 300

    tempdeck.set_temperature(temp_a)
    update_log_file()

    # setup samples
    current_status = "setup samples and proteinase K"
    sources = [
                  well for rack in source_racks for well in rack.wells()][:NUM_SAMPLES]
    max_sample_per_set = len(sources)
    set_of_samples = math.ceil(NUM_SAMPLES / max_sample_per_set)

    # setup proteinase K
    num_cols = math.ceil(NUM_SAMPLES / 8)
    num_pk_strips = math.ceil(PK_VOLUME * num_cols * liquid_headroom / pk_capacity)
    pk_cols_per_strip = math.ceil(num_cols / num_pk_strips)

    prot_K_strips = strips_block.rows()[0][:num_pk_strips]
    ctx.comment("Proteinase K: using {} strips with at least {:.2f} uL each".format(num_pk_strips,
                                                                                    pk_cols_per_strip * PK_VOLUME * liquid_headroom))

    # setup destinations
    dests_single = dest_plate.wells()[:NUM_SAMPLES]
    dests_multi = dest_plate.rows()[0][:math.ceil(NUM_SAMPLES / 8)]

    tip_log = {'count': {}}
    tip_file_path = folder_path + '/tip_log.json'
    if TIP_TRACK and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips1000' in data:
                    tip_log['count'][p1000] = data['tips1000']
                else:
                    tip_log['count'][p1000] = 0
                if 'tips20' in data:
                    tip_log['count'][m20] = data['tips20']
                else:
                    tip_log['count'][m20] = 0
    else:
        tip_log['count'] = {p1000: 0, m20: 0}

    tip_log['tips'] = {
        p1000: [tip for rack in tipracks1000 for tip in rack.wells()],
        m20: [tip for rack in tipracks20 for tip in rack.rows()[0]]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [p1000, m20]
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

    lysis_total_vol = LYSIS_VOLUME * NUM_SAMPLES * liquid_headroom
    beads_total_vol = BEADS_VOLUME * NUM_SAMPLES * liquid_headroom

    ctx.comment("Lysis buffer expected volume: {} mL".format(lysis_total_vol / 1000))
    ctx.comment("Beads expected volume: {} ul each".format(beads_total_vol / 8))

    radius = lys_buff.diameter / 2
    heights = {lys_buff: lysis_total_vol / (math.pi * (radius ** 2))}
    ctx.comment("Lysis buffer expected initial height: {:.2f} mm".format(heights[lys_buff]))
    min_h = 5

    def h_track(tube, vol, context):
        nonlocal heights
        dh = vol / (math.pi * (radius ** 2))
        if heights[tube] - dh > min_h:
            heights[tube] = heights[tube] - dh
        else:
            heights[tube] = min_h
        context.comment("Going {} mm deep".format(heights[tube]))
        return tube.bottom(heights[tube])

    update_log_file()

    # transfer beads
    current_status = "transfer beads"
    for idx, d in enumerate(dests_multi):
        pick_up(m20)
        # transferring beads
        # no air gap to use 1 transfer only avoiding drop during multiple transfers.
        m20.transfer(BEADS_VOLUME, beads, d.bottom(2), air_gap=5,
                     new_tip='never')
        m20.mix(2, 20, d.bottom(2))
        m20.air_gap(5)
        m20.drop_tip()

    update_log_file()
    ctx.comment('Move deepwell plate to Station B for RNA extraction.')

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips1000': tip_log['count'][p1000],
            'tips20': tip_log['count'][m20]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

    current_status = "protocol A part 2 finished"
    update_log_file()
