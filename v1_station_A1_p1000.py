from opentrons import protocol_api
import json
import os
import math
import time
import datetime

# metadata
metadata = {
    'protocolName': 'Version 1 S9 Station A part 1 BP Purebase',
    'author': 'Agostino, Marco, Nick and Team 2',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}

NUM_SAMPLES = 96
SAMPLE_VOLUME = 200
LYSIS_VOLUME = 160
IEC_VOLUME = 19
TIP_TRACK = True  # Tracking of the tips

DEFAULT_ASPIRATE = 100
DEFAULT_DISPENSE = 100

LYSIS_RATE_ASPIRATE = 100
LYSIS_RATE_DISPENSE = 100

ic_headroom = 1.1
ic_capacity = 180

"""Variables for the temperature check"""
temp_a = 3.9  # we will set the temp 0.1 less in order to make a check more safe
temp_check = 4.0
TempUB = temp_check + 0.3  # It is fixed the warning if we go over 0.3


def run(ctx: protocol_api.ProtocolContext):
    # Define the Path for the logs
    folder_path = '/var/lib/jupyter/notebooks/outputs'
    temp_file_path = folder_path + '/completion_log.json'
    Log_Dict = {"stages": []}  # For log file data
    current_status = "Setting environment"

    def update_log_file(message="Step executed successfully", check_temperature=True):
        current_Log_dict = {"stage_name": current_status,
                            "time": datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S:%f"),
                            "temp": None,
                            "message": message}
        if check_temperature:
            current_Log_dict["temp"] = tempdeck.temperature
            if tempdeck.temperature >= TempUB and tempdeck.status != 'holding at target':
                if tempdeck.status != 'holding at target':
                    ctx.pause('The temperature is above {}°C'.format(TempUB))
                    while tempdeck.temperature >= temp_check:
                        print("sleeping for 0.5 s to wait for Temp_Deck")
                        print("current temperature is {}°C".format(tempdeck.temperature))
                        time.sleep(0.1)

    ctx.comment("Station A protocol for {} COPAN 330C samples.".format(NUM_SAMPLES))
    # load labware
    tempdeck = ctx.load_module('Temperature Module Gen2', '10')
    tempdeck.set_temperature(temp_a)
    internal_control_labware = tempdeck.load_labware(
       'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
       'chilled tubeblock for internal control (strip 1)')
    # Added Custom Labware inside the protocol
    with open('/var/lib/jupyter/notebooks/COPAN 15 Tube Rack 14000 µL.json', 'r') as source_file:
        source_def = json.load(source_file)
    source_racks = [ctx.load_labware_from_definition(source_def, slot, 'source tuberack' + ' ' + str(i+1))
                    for i, slot in enumerate(['2', '3', '5', '6'])]
    dest_plate = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', '1', '96-deepwell sample plate')
    lys_buff = ctx.load_labware(
        'opentrons_6_tuberack_falcon_50ml_conical', '4',
        '50ml tuberack for lysis buffer + PK (tube A1)').wells()[0]
    tipracks300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot,
                                    '200ul filter tiprack')
                   for slot in ['8', '9', '11']]
    tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '7',
                                   '20µl filter tiprack')]

    # load pipette
    m20 = ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=tipracks20)
    p300 = ctx.load_instrument(
        'p300_single_gen2', 'right', tip_racks=tipracks300)
    p300.flow_rate.blow_out = 300
    # setup samples

    """"we try to allocate the maximum number of samples available in racks (e.g. 15*number of racks)
    and after we will ask the user to replace the samples to reach NUM_SAMPLES
    if number of samples is bigger than samples in racks."""

    sources = [
        well for rack in source_racks for well in rack.wells()][:NUM_SAMPLES]
    max_sample_per_set = len(sources)
    set_of_samples = math.ceil(NUM_SAMPLES/max_sample_per_set)

    # setup destinations
    dests_single = dest_plate.wells()[:NUM_SAMPLES]
    dests_multi = dest_plate.rows()[0][:math.ceil(NUM_SAMPLES/8)]

    tip_log = {'count': {}}
    tip_file_path = folder_path + '/tip_log.json'
    if TIP_TRACK and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips1000' in data:
                    tip_log['count'][p300] = data['tips1000']
                else:
                    tip_log['count'][p300] = 0
                if 'tips20' in data:
                    tip_log['count'][m20] = data['tips20']
                else:
                    tip_log['count'][m20] = 0
    else:
        tip_log['count'] = {p300: 0, m20: 0}

    tip_log['tips'] = {
        p300: [tip for rack in tipracks300 for tip in rack.wells()],
        m20: [tip for rack in tipracks20 for tip in rack.rows()[0]]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [p300, m20]
    }

    # setup internal control	
    num_cols = math.ceil(NUM_SAMPLES/8)
    num_ic_strips = math.ceil(IEC_VOLUME * num_cols * ic_headroom / ic_capacity)
    ic_cols_per_strip = math.ceil(num_cols / num_ic_strips)
    
    internal_control_strips = internal_control_labware.rows()[0][:num_ic_strips]
    ctx.comment("Internal Control: using {} strips with at least {:.2f} uL each".format(
        num_ic_strips, ic_cols_per_strip * IEC_VOLUME * ic_headroom))

    def pick_up(pip):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip]:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
        tip_log['count'][pip] += 1

    lysis_total_vol = LYSIS_VOLUME * NUM_SAMPLES

    ctx.comment("Lysis buffer expected volume: {} mL".format(lysis_total_vol/1000))
    
    radius = lys_buff.diameter/2
    heights = {lys_buff: lysis_total_vol/(math.pi*(radius**2))}
    ctx.comment("Lysis buffer expected initial height: {:.2f} mm".format(heights[lys_buff]))
    min_h = 5

    def h_track(tube, vol, context):
        nonlocal heights
        dh = vol/(math.pi*(radius**2))
        if heights[tube] - dh > min_h:
            heights[tube] = heights[tube] - dh
        else:
            heights[tube] = min_h
        context.comment("Going {} mm deep".format(heights[tube]))
        return tube.bottom(heights[tube])

    # transfer sample
    current_status = "transfer sample"
    done_samples = 0
    refill_of_samples = set_of_samples - 1  # the first set is already filled before start
    ctx.comment("Using {} samples per time".format(max_sample_per_set))
    ctx.comment("We need {} samples refill.".format(refill_of_samples))
    update_log_file()

    current_status = "setup samples"
    # for i in range(set_of_samples):
    #     # setup samples
    #     remaining_samples = NUM_SAMPLES - done_samples
    #     ctx.comment("Remaining {} samples".format(remaining_samples))
    #     # just eventually pick the remaining samples if less than full rack
    #     set_of_sources = sources[:remaining_samples]
    #     destinations = dests_single[done_samples:(done_samples + len(sources))]
    #
    #     ctx.comment("Transferring {} samples".format(len(sources)))
    #
    #     for s, d in zip(sources, destinations):
    #         pick_up(p300)
    #         p300.mix(5, 150, s.bottom(6))
    #         p300.transfer(SAMPLE_VOLUME, s.bottom(6), d.bottom(5), air_gap=100, new_tip='never')
    #         p300.air_gap(100)
    #         p300.drop_tip()
    #
    #     done_samples = done_samples + len(sources)
    #     ctx.comment("Done {} samples".format(done_samples))
    #
    #     if i < refill_of_samples:
    #         ctx.pause("Please refill samples")
    #
    # update_log_file()
    # # transfer lysis buffer + proteinase K and mix
    # current_status = "transfer lysis buffer + proteinase K and mix"
    # p300.flow_rate.aspirate = LYSIS_RATE_ASPIRATE
    # p300.flow_rate.dispense = LYSIS_RATE_DISPENSE
    # for s, d in zip(sources, dests_single):
    #     pick_up(p300)
    #     p300.transfer(LYSIS_VOLUME, h_track(lys_buff, LYSIS_VOLUME, ctx), d.bottom(5), air_gap=100,
    #                    mix_after=(10, 100), new_tip='never')
    #     p300.air_gap(100)
    #     p300.drop_tip()

    print('Incubate sample plate (slot 4) at 55-57˚C for 20 minutes. \
    Return to slot 4 when complete.')
    update_log_file()
    current_status = "Go in part 2"
    update_log_file()
#     ctx.pause('Incubate sample plate (slot 4) at 55-57˚C for 20 minutes. \
# Return to slot 4 when complete.')

    """Starting part 2 of the protocol"""

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips1000': tip_log['count'][p300],
            'tips20': tip_log['count'][m20]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)
