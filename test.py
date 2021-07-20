import sys
import os
import argparse
import ntplib
import time

from concurrent.futures import ThreadPoolExecutor
import asyncio
from scipy.interpolate import interp1d 
print(os.getcwd())
# import System
# from System import String

sys.path.append(r'../lib')
sys.path.append(r'lib')
sys.path.append(r'..')
sys.path.append(r'../alicptfts')
sys.path.append(r'../alicptfts/alicptfts')

import numpy as np
import random
import time 
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

import nidaqmx
from nidaqmx.stream_readers import AnalogSingleChannelReader
from nidaqmx.stream_writers import AnalogSingleChannelWriter

# import lib.MC2000B_COMMAND_LIB as mc2000b
# import MC2000B_COMMAND_LIB as mc2000b
#from mynewportxps import NewportXPS
from mynewportxps.newportxps import NewportXPS
from mynewportxps.newportxps.XPS_C8_drivers import XPSException
#from mynewportxps.newportxps.XPS_C8_drivers import XPSException
from mynewportxps.newportxps.newportxps import withConnectedXPS
from alicptfts.alicptfts import AlicptFTS
import posixpath

import enum
groupName = {'PointingLinear': 'Group2',
    'PointingRotary': 'Group3',
    'MovingLinear': 'Group1'}

##### START RASTOR SCANNER CODE

def convert_to_rastor(x_stamps, y_stamps, v_stamps):
    x_times, x_pos = x_stamps
    y_times, y_pos = y_stamps 
    v_times, v_pos = v_stamps 
    interpx = interp1d(x_times, x_pos)
    interpy = interp1d(y_times, y_pos)
    interpv = interp1d(v_times, v_pos)

    max_y = max(y_pos)
    max_x = max(x_pos)
    min_y = min(y_pos)
    min_x = min(x_pos)
    x_range = int(max_x-min_x)+1
    y_range = int(max_y-min_y)+1

    rastor = np.zeros((x_range, y_range))
    max_x_time = max(x_times)
    max_y_time = max(y_times)
    min_x_time = min(x_times)
    min_y_time = min(y_times)
    for t in v_times:
        if(t < min_x_time or t < min_y_time):
            continue
        if(t > max_x_time or t > max_y_time):
            continue
        v = interpv(t)
        x = interpx(t)
        y = interpy(t)
        rastor[int(x-min_x), int(y-min_y)] = v 
    plt.imshow(rastor)
    plt.show()

def nidaqmx_single_read(time_length, time_resolution, channel='ai0', tasknumber=1):
    times = []
    readings = []
    n = 0
    taskname = 'Dev' + str(tasknumber)
    voltage_channel = '/'.join([taskname, channel])
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(voltage_channel)
        time0 = time.time()
        time_elapsed = time.time()-time0 
        #print(time_elapsed)
        while(time_elapsed < time_length):
            if(n%10 == 0):
                print('Reading sample ' + str(n))
            time_start = time.time()
            x = task.read() 
            time_end = time.time()
            times.append((time_start + time_end)/2)
            readings.append(x)
            time.sleep(time_resolution)
            n+=1
            time_elapsed = time.time()-time0 
    return times, readings

def read_positions(fts, socket, time_length, time_resolution, group_name):
    times = []
    readings = []
    time0 = time.time()
    time_elapsed = time.time() - time0 
    n = 0
    while(time_elapsed < time_length):
        if(n%10 == 0):
            print('Reading sample ' + str(n))
        time_start = time.time()
        x = fts.newportxps.get_stage_position(group_name + '.Pos', socket)
        time_end = time.time()
        #print(time_start)
        #print(time_end)
        times.append((time_start + time_end)/2)
        readings.append(x)
        time.sleep(time_resolution)
        n+=1
        time_elapsed = time.time()-time0 
    return times, readings


def plot_readings_timestamps(readings, timestamps,readings2, timestamps2,  channel, channel2,pos, pos_times, pos2, pos_times2):
    utc_list = [datetime.utcfromtimestamp(t) for t in timestamps]
    utc_list2 = [datetime.utcfromtimestamp(t) for t in timestamps2]
    utc_pos = [datetime.utcfromtimestamp(t) for t in pos_times]
    utc_pos2 = [datetime.utcfromtimestamp(t) for t in pos_times2]
    plt.plot(utc_list, [-r for r in readings], label='Voltage (V) in channel ' + str(channel))
    plt.plot(utc_list2, [-r for r in readings2], label='Voltage (V) in channel ' + str(channel2))
    plt.plot(utc_pos, [p/100 for p in pos], label='group1 position/100')
    plt.plot(utc_pos2, [p/100 for p in pos2], label='group2 position/100')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Value')
    plt.legend()
    plt.show()

def initialize_fts(password, num_sockets):
    print('Initializing FTS')
    fts = AlicptFTS()
    varlist = []

    for i in ['Position', 'Velocity', 'Acceleration']:
        for j in ['Current', 'Setpoint']:
            for n in range(3):
                varlist.append('Group'+str(n)+'.Pos.'+j + i)
    x = fts.initialize('192.168.254.254','Administrator', password)

    print('Status: Finish initialization')
    fts.status()
    return fts

def move_group(fts, pos, socket):
    for p in pos:
        pos_spec = p.split('.')
        if pos_spec[0] == 'g1':
            fts.newportxps.move_stage(groupName['MovingLinear']+'.Pos', int(pos_spec[1]), False, socket=socket)
        elif pos_spec[0] == 'g2':
            fts.newportxps.move_stage(groupName['PointingLinear']+'.Pos', int(pos_spec[1]), False, socket=socket)
    return

def move_group1(fts, pos, socket):
    '''
    pos: list of int and str
    '''
    for p in pos:
        if type(p) == str:
            time.sleep(int(p))
        else:
            fts.newportxps.move_stage(groupName['MovingLinear']+'.Pos', p ,False, socket=socket)
    return 

def move_group2(fts, pos, socket):
    for p in pos:
        if type(p) == str:
            time.sleep(int(p))
        else:
            fts.newportxps.move_stage(groupName['PointingLinear']+'.Pos', p ,False, socket=socket)
    return 

def get_pos1(fts, socket):
    pos = fts.newportxps.get_stage_position('Group1.Pos', socket=socket)
    return pos

def get_pos2(fts, socket):
    pos = fts.newportxps.get_stage_position('Group2.Pos', socket=socket)
    return pos

def write_seq(min1, max1, min2, max2):
    # min1, max1, min2, max2 are all int
    seq = ['g2.' + str(min2), 'g1.' + str(min1)]
    for i in range(min2+1, max2+1):
        if i % 2 == min2 % 2:
            seq.append('g1.' + str(min1))
        else:
            seq.append('g1.' + str(max1))
        seq.append('g2.' + str(i))
    return seq

def calc_time(g1_min, g1_max, g2_min, g2_max):
    total_min = -145
    total_max = 145
    total_time = 15
    total_range = total_max-total_min 
    
    velocity = total_range/total_time 
    sweep_time = (g1_max-g1_min)/velocity 
    num_sweeps = g2_max - g2_min 
    total_sweep_time = sweep_time * num_sweeps 
    sweep_move_time = (g2_max-g2_min)/velocity 
    homing_time = 20

    return total_sweep_time + sweep_move_time + homing_time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password', help='Password to connect to the NewportXPS')
    args = parser.parse_args()
    password = args.password

    fts = initialize_fts(password, num_sockets = 6)
    g1_min = -95
    g1_max = 118
    g2_min = -145
    g2_max = 140
    seq = write_seq(g1_min, g1_max, g2_min, g2_max)
    #seq = ['g2.-80', 'g1.-145', 'g1.145', 'g2.-40', 'g1.-145', 'g2.0', 'g1.145', 'g2.60', 'g1.-145', 'g2.120', 'g1.145', 'g2.-30', 'g1.0']
    #seq1 = [-145, 145, -145, 145]#, 10, 300, 8]
    #seq2 = [-120, 0, 110]#, 10, 300, 10, 400, 10]
    time_length = calc_time(g1_min, g1_max, g2_min, g2_max)
    time_resolution = 0.01
    channel = 'ai0'
    channel2 = 'ai4'
    with ThreadPoolExecutor(max_workers=4) as executor:
        
        g = executor.submit(move_group, fts, seq, socket=0)
        #a = executor.submit(move_group1, fts,seq1 , socket=0)
        #b = executor.submit(move_group2, fts,seq2 , socket=1)
        e = executor.submit(nidaqmx_single_read, time_length, time_resolution, channel, 1)
        c = executor.submit(read_positions, fts, 2, time_length, time_resolution, 'Group1')
        d = executor.submit(read_positions, fts, 3, time_length, time_resolution, 'Group2')
        
    
        nida_times, readings = e.result()
        nida_times2, readings2 = [],[]#f.result()
        pos1_times,pos1  = c.result()
        pos2_times,pos2 = d.result()

    x_pos = (pos1_times, pos1)
    y_pos = (pos2_times, pos2)
    volts = (nida_times, readings)
    #x_pos, y_pos, volts are tuples

    convert_to_rastor(x_pos, y_pos, volts)
    #plot_readings_timestamps(readings, nida_times,nida_times2, readings2,channel,channel2, pos1, pos1_times, pos2, pos2_times)
    
### END RASTOR SCANNING CODE

##########################
## START FTS CODE
##########################
def set_trigger_start(fts, groupname, socket=0, verbose=False):
    trigger = 'SGamma.MotionStart'
    event_name = '.'.join([groupname, trigger])
    err, ret = fts.newportxps._xps.EventExtendedConfigurationTriggerSet(socket, [event_name], ['0'],['0'],['0'],['0'])
    fts.newportxps.check_error(err, msg='EventConfigTrigger')
    if verbose:
        print( " EventExtended Trigger Set ", ret)
    return 

def configure_gathering(fts, groupnames, datanames = ['SetpointPosition'], socket=0, verbose=False):
    gather_titles = []
    for g in groupnames:
        for d in datanames:
            title = '.'.join([g, d])
            gather_titles.append(title)
    err, ret = fts.newportxps._xps.GatheringConfigurationSet(socket, gather_titles)
    fts.newportxps.check_error(err, msg='GatherConfigSet')
    if verbose:
        print( " Gather Config Set ", ret)
    return gather_titles

def configure_gathering_length(fts, run_time, collection_resolution, socket=0, verbose=False):
    action_name = 'GatheringRun'
    milli_to_sec = 1000 # 1000 milliseconds in a second
    run = int(run_time * milli_to_sec) 
    milli_to_servo = 10000 # each servo cycle is 1/8000 sec
    servo_cycle = int(collection_resolution * milli_to_servo)

    err, ret = fts.newportxps._xps.EventExtendedConfigurationActionSet(socket, [action_name], 
                                                [str(run)], [str(servo_cycle)], ['0'], ['0'])
    fts.newportxps.check_error(err, msg='GatherConfigSet')
    if verbose:
        print( " Gather Run Set ", ret)
    return 

def cycle_group(fts, groupname, start, end, numcycles, socket=0):
    for i in range(numcycles):
        err, ret = fts.newportxps._xps.GroupMoveAbsolute(socket, groupname, [start])
        err, ret = fts.newportxps._xps.GroupMoveAbsolute(socket, groupname, [end])

def calc_time(movement_params):
    # TODO write this
    return 80 # seconds


def gather_data_setup(fts, gather_time, gather_resolution, groupnames):
    axname = 'Pos'
    
    groups = ['.'.join([g, axname]) for g in groupnames]
    trigger_start_group = groups[0]

    group_titles = configure_gathering(fts, groups, verbose=True)
    set_trigger_start(fts, trigger_start_group, verbose=True)
    configure_gathering_length(fts, gather_time, gather_resolution, verbose=True)
    eventID, m = fts.newportxps._xps.EventExtendedStart(0)
    return trigger_start_group, group_titles,groups, eventID

def perform_movement(fts, movement_params, trigger_start_group, group_titles, groups):
    socket=0
    numcycles = movement_params['num_cycles']
    cycle_range = movement_params['cycle_range']
    vel = movement_params['velocity']
    accel = movement_params['acceleration']
    config_list1 = movement_params['config_list1']
    config_list2 = movement_params['config_list2']

    ## TODO: read in instead of hard code
    group2_max_accel = 600
    group3_max_accel = 80
    group2_max_vel = 200
    group3_max_vel = 20
    fts.newportxps._xps.PositionerSGammaVelocityAndAccelerationSet(socket, groups[0],vel,accel)
    fts.newportxps._xps.PositionerSGammaVelocityAndAccelerationSet(socket, groups[1],group2_max_vel,group2_max_accel)
    fts.newportxps._xps.PositionerSGammaVelocityAndAccelerationSet(socket, groups[2],group3_max_vel,group3_max_accel)
    time0 = time.time()
    for pos1 in config_list1:
        for pos2 in config_list2:
            print(str(pos1) + ' ' + str(pos2))
            err, ret = fts.newportxps._xps.GroupMoveAbsolute(socket, groups[1], [pos1])
            err, ret = fts.newportxps._xps.GroupMoveAbsolute(socket, groups[2], [pos2])
            cycle_group(fts, trigger_start_group, start=cycle_range[0], end=cycle_range[1], numcycles=numcycles)
    time1 = time.time()
    timestamp = 'Time start: %f, Time end: %f, Time diff: %f' % (time0, time1, time1-time0)
    headers=[timestamp, str(group_titles)]
    return headers

def determine_num_chunks(fts, total_lines, socket=0, max_lines=1000):
    nchunks = int(total_lines/max_lines)+1
    num_lines = total_lines 
    success = False
    while(not success):
        print('Current number of chunks ' + str(nchunks))
        ret, _ = fts.newportxps._xps.GatheringDataMultipleLinesGet(socket, 0, int(num_lines))
        print('Current number of lines ' + str(num_lines))
        if(ret < 0):
            nchunks += 2
            num_lines = total_lines/nchunks 
        else:
            print('Success')
            success = True 
        
        if(num_lines < 10):
            raise AttributeError('XPS not reading even though small enough chunks')
    return nchunks 

def read_and_save(fts, filename, headers, socket=0):
    ret, total_lines, max_lines = fts.newportxps._xps.GatheringCurrentNumberGet(socket)
    nchunks = determine_num_chunks(fts, total_lines, socket)
    print('Number of chunks: ' + str(nchunks))
    lines_per_chunk = int(total_lines/nchunks)
    remaining_lines = total_lines - lines_per_chunk*nchunks
    with open(filename, 'w') as f:
        for header in headers:
            f.write("## " + header + "\n")
        for i in range(nchunks):
            start = lines_per_chunk*i 
            ret, buffer = fts.newportxps._xps.GatheringDataMultipleLinesGet(socket, start, lines_per_chunk)
            f.write(buffer)
        start = lines_per_chunk * nchunks
        ret, buffer = fts.newportxps._xps.GatheringDataMultipleLinesGet(socket, start, remaining_lines)
        f.write(buffer)
    return 

def gather_data_end_and_save(fts, gather_filename, headers, eventID, socket=0):
    ret = fts.newportxps._xps.EventExtendedRemove(socket, eventID)
    ret = fts.newportxps._xps.GatheringStopAndSave(socket)
    
    read_and_save(fts, gather_filename, headers)

def gather_data(fts, movement_params, group_order, gather_filename = 'testgather.dat'):
    gather_time = movement_params['gather_time']
    gather_resolution = movement_params['resolution']
    trigger_start_group, group_titles,groups, eventID = gather_data_setup(fts, gather_time, gather_resolution, group_order)
    
    headers = perform_movement(fts, movement_params, trigger_start_group, group_titles,groups)

    gather_data_end_and_save(fts, gather_filename, headers, eventID)
    return 

def fts_position_scan(fts, output_file, resolution, group_order=['Group1', 'Group2', 'Group3'],
                        num_cycles=5, cycle_range=(0, 500), 
                        velocity=20, acceleration=300,
                        config1_list=[0, 100, 200, 300, 400, 500], 
                        config2_list=[0, 90, 180, 270]):
    movement_params = {}
    
    movement_params['resolution'] = resolution
    movement_params['num_cycles'] = num_cycles
    movement_params['cycle_range'] = cycle_range
    movement_params['velocity'] = velocity
    movement_params['acceleration'] = acceleration
    movement_params['config_list1'] = config1_list
    movement_params['config_list2'] = config2_list

    movement_params['gather_time'] =  calc_time(movement_params) 
    gather_data(fts, movement_params, group_order, gather_filename=output_file)

    return 
################################
## END FTS CODE
################################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password', help='Password to connect to the NewportXPS')
    args = parser.parse_args()
    password = args.password
    gather_filename = 'test_gather.dat'
    fts = initialize_fts(password, num_sockets = 6)
    
    #scan_plate(fts)
    fts_position_scan(fts, gather_filename, 0.001, cycle_range=(20, 40), velocity=100, 
                        config1_list=[30, 100, 200, 400], config2_list=[2], num_cycles=10)
    fts.close()
 

def graph_position_data(dat_filename, sep=';'):
    ## ignores commented lines
    ## assumes each line is separated by semicolons
    
    df = pd.read_csv(dat_filename, sep=';', comment='#', header=None)
    plt.figure()
    for col in df:
        pos_list = df[col].tolist()
        plt.plot(pos_list, label = col)
    plt.legend()
    plt.show()
    return 
if __name__ == '__main__':
    #convert_to_rastor(([1, 2, 3, 7],[4, 5, 6, 10]),([1, 5, 7],[2, 3, 4]),([7, 5, 3, 1],[1,2,3,4]))
    main()
    graph_position_data('test_gather.dat')
  
    
def stream_test():
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
        #task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
        #writer = AnalogSingleChannelWriter(task.out_stream)
        reader = AnalogSingleChannelReader(task.in_stream)
        '''
        values_to_test = np.array(
                    [random.random() for _ in
                     range(100)])
    
        print(values_to_test)
        task.start()
        #x = writer.write_many_sample(values_to_test)
        task.stop()
        '''
        values_read = np.zeros(100)
        task.start()
        x = reader.read_many_sample(values_read, number_of_samples_per_channel=100)
        task.stop()
        print(values_read)
        print(x)