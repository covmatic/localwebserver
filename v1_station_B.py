from opentrons.types import Point
import json
import os
import math
import threading
from time import sleep
import datetime

metadata = {
    'protocolName': 'Version 1 S9 Station B BP Purebase (400µl sample input)',
    'author': 'Nick <ndiehl@opentrons.com',
    'apiLevel': '2.3'
}

NUM_SAMPLES = 8  # start with 8 samples, slowly increase to 48, then 94 (max is 94)
SAMPLE_VOL = 400
ELUTION_VOL = 40
TIP_TRACK = False
CHECK_TEMP = True
PARK = False

SKIP_DELAY = False

# Definitions for deck light flashing
class CancellationToken:
    def __init__(self):
       self.is_continued = False

    def set_true(self):
       self.is_continued = True

    def set_false(self):
       self.is_continued = False


def turn_on_blinking_notification(hardware, pause):
    while pause.is_continued:
        hardware.set_lights(rails=True)
        sleep(1)
        hardware.set_lights(rails=False)
        sleep(1)

def create_thread(ctx, cancel_token):
    t1 = threading.Thread(target=turn_on_blinking_notification, args=(ctx._hw_manager.hardware, cancel_token))
    t1.start()
    return t1


# Start protocol
def run(ctx):
    # Setup for flashing lights notification to empty trash
    cancellationToken = CancellationToken()

    # load labware and pipettes
    num_cols = math.ceil(NUM_SAMPLES/8)
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot, '200µl filtertiprack')
               for slot in ['3', '6', '8', '9', '10']]
    if PARK:
        parkingrack = ctx.load_labware(
            'opentrons_96_tiprack_300ul', '7', 'empty tiprack for parking')
        parking_spots = parkingrack.rows()[0][:num_cols]
    else:
        tips300.append(ctx.load_labware('opentrons_96_tiprack_300ul', '7',
                                        '200µl filtertiprack'))
        parking_spots = [None for none in range(12)]

    m300 = ctx.load_instrument(
        'p300_multi_gen2', 'left', tip_racks=tips300)

    magdeck = ctx.load_module('Magnetic Module Gen2', '4')
    magdeck.disengage()
    magheight = 13.7
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep')
    # magplate = magdeck.load_labware('biorad_96_wellplate_200ul_pcr')
    tempdeck = ctx.load_module('Temperature Module Gen2', '1')
    flatplate = tempdeck.load_labware(
                'opentrons_96_aluminumblock_nest_wellplate_100ul',)
    waste = ctx.load_labware('nest_1_reservoir_195ml', '11',
                             'Liquid Waste').wells()[0].top()
    etoh = ctx.load_labware(
        'nest_1_reservoir_195ml', '2', 'Trough with Ethanol').wells()[:1]
    res12 = ctx.load_labware(
                    'nest_12_reservoir_15ml', '5', 'Trough with Reagents')
    binding_buffer = res12.wells()[:2]
    wash1 = res12.wells()[3:7]
    wash2 = res12.wells()[7:11]
    water = res12.wells()[11]

    mag_samples_m = magplate.rows()[0][:num_cols]
    elution_samples_m = flatplate.rows()[0][:num_cols]

    magdeck.disengage()  # just in case
    tempdeck.set_temperature(4)
    # tempdeck.await_temperature(4)  # just in case it is slow to arrive at that temp

    m300.flow_rate.aspirate = 50
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300

    folder_path = './outputs/B'
    tip_file_path = folder_path + '/tip_log.json'
    tip_log = {'count': {}}
    if TIP_TRACK and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips300' in data:
                    tip_log['count'][m300] = data['tips300']
                else:
                    tip_log['count'][m300] = 0
        else:
            tip_log['count'][m300] = 0
    else:
        tip_log['count'] = {m300: 0}

    tip_log['tips'] = {
        m300: [tip for rack in tips300 for tip in rack.rows()[0]]}
    tip_log['max'] = {m300: len(tip_log['tips'][m300])}

    if CHECK_TEMP:
        temp_file_path = folder_path + '/temp_log.json'
        TempUB = 5  # Upper bound on allowable temperature
        Tempflag = 0  # Generates log file in case temperature exceeds bound
        TempLog = {"time": [], "value": []}  # For log file data
        if tempdeck.temperature >= TempUB:
            ctx.pause('The temperature is above 5°C')
            tempdeck.await_temperature(4)  # Wait that it reaches 4°C
            ctx.resume()
            Tempflag = 1
            TempLog["time"].append(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S:%f"))
            TempLog["value"].append(tempdeck.temperature)  # Generates Log file data

    def pick_up(pip, loc=None):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
            tip_log['count'][pip] += 1

    switch = True
    drop_count = 0
    drop_threshold = 120  # number of tips trash will accommodate before prompting user to empty

    def drop(pip):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch
        drop_count += 8
        if drop_count == drop_threshold:
            # Setup for flashing lights notification to empty trash
            if not ctx._hw_manager.hardware.is_simulator:
                cancellationToken.set_true()
            thread = create_thread(ctx, cancellationToken)
            ctx.pause('Please empty tips from waste before resuming.')

            ctx.home()  # home before continuing with protocol
            cancellationToken.set_false()  # stop light flashing after home
            thread.join()
            drop_count = 0

    def remove_supernatant(vol, park=False):
        m300.flow_rate.aspirate = 30
        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            if park:
                pick_up(m300, spot)
            else:
                pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.5).move(Point(x=side*2))
            for _ in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, m.top())  # void air gap if necessary
                m300.move_to(m.center())
                m300.transfer(vol_per_trans, loc, waste, new_tip='never',
                              air_gap=20)
                m300.blow_out(waste)
                m300.air_gap(20)
            drop(m300)
        m300.flow_rate.aspirate = 150

    def bind(vol, park=True):
        # add bead binding buffer and mix samples
        for i, (well, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            source = binding_buffer[i//(12//len(binding_buffer))]
            pick_up(m300)
            for _ in range(5):
                m300.aspirate(180, source.bottom(0.5))
                m300.dispense(180, source.bottom(5))
            num_trans = math.ceil(vol/210)
            vol_per_trans = vol/num_trans
            for t in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, source.top())  # void air gap if necessary
                m300.transfer(vol_per_trans, source, well.top(), air_gap=20,
                              new_tip='never')
                if t == 0:
                    m300.air_gap(20)
            m300.mix(5, 200, well)
            m300.blow_out(well.top(-2))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                drop(m300)

        if not SKIP_DELAY:
            # Time Issue in Station B Waiting time of 5 min before magnetic module activation.
            ctx.delay(minutes=5, msg='Waiting 5 minutes before MagDeck activation.')

        magdeck.engage(height=magheight)

        if not SKIP_DELAY:
            #Time Issue in Station B After the waiting time of 5 min the magnetic module should run for 6 min.
            ctx.delay(minutes=6, msg='Incubating on MagDeck for 6 minutes.')

        # remove initial supernatant
        remove_supernatant(vol+SAMPLE_VOL, park=park)

    def wash(wash_vol, source, mix_reps, park=True):
        magdeck.disengage()

        num_trans = math.ceil(wash_vol/200)
        vol_per_trans = wash_vol/num_trans
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            src = source[i//(12//len(source))]
            for n in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, src.top())
                m300.transfer(vol_per_trans, src, m.top(), air_gap=20,
                              new_tip='never')
                if n < num_trans - 1:  # only air_gap if going back to source
                    m300.air_gap(20)
            m300.mix(mix_reps, 150, loc)
            m300.blow_out(m.top())
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                drop(m300)

        magdeck.engage(height=magheight)
        ctx.delay(minutes=5, msg='Incubating on MagDeck for 5 minutes.')

        remove_supernatant(wash_vol, park=park)

    def elute(vol, park=True):
        # resuspend beads in elution
        for i, (m, spot) in enumerate(zip(mag_samples_m, parking_spots)):
            pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.aspirate(40, water)
            m300.move_to(m.center())
            m300.dispense(40, loc)
            m300.mix(10, 30, loc)
            m300.blow_out(m.bottom(5))
            m300.air_gap(20)
            if park:
                m300.drop_tip(spot)
            else:
                drop(m300)

        ctx.delay(minutes=2, msg='Incubating off magnet at room temperature \
for 2 minutes')
        magdeck.engage(height=magheight)
        ctx.delay(minutes=2, msg='Incubating on magnet at room temperature \
for 2 minutes')

        for i, (m, e, spot) in enumerate(
                zip(mag_samples_m, elution_samples_m, parking_spots)):
            # my modification for temp: SHOULD BE CHECKED BECAUSE ON STATION A-B THE SIM. FAILS FOR HEIGHT ERROR
            if tempdeck.temperature >= 5:
            # if CHECK_TEMP:  # It is needed to simulate on the computer otherwise is always empty
                ctx.pause('The temperature is above the limits')
                tempdeck.await_temperature(4)  # not sure if needed or we break the protocol
                ctx.resume()
                Tempflag = 1
                TempLog["time"].append(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                TempLog["value"].append(tempdeck.temperature)  # Generates Log file data
            # set_completed modification
            if park:
                pick_up(m300, spot)
            else:
                pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.transfer(40, loc, e.bottom(5), air_gap=20, new_tip='never')
            m300.blow_out(e.top(-2))
            m300.air_gap(20)
            m300.drop_tip()

    bind(210, park=PARK)
    wash(500, wash1, 20, park=PARK)
    wash(500, wash2, 20, park=PARK)
    wash(800, etoh, 4, park=PARK)

    magdeck.disengage()
    ctx.delay(minutes=5, msg='Airdrying beads at room temperature for 5 \
minutes.')

    elute(40, park=PARK)
    # Printing the Temperatures
    if CHECK_TEMP:
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        with open(temp_file_path, 'w') as outfiletemp:
            json.dump(TempLog, outfiletemp)
