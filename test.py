import sys
import os
import argparse
import ntplib
import time
import csv

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


def initialize_fts(password, num_sockets, IP):
    print('Initializing FTS')
    fts = AlicptFTS()
    x = fts.initialize(IP,'Administrator', password)
    for i in range(num_sockets):
        fts.newportxps.connect()

    print('Status: Finish initialization')
    fts.status()
    return fts
    
def HexapodMoveAbsolute(GroupName=None, CoordinateSystem=None, 
                            X=0, Y=0, Z=0, U=0, V=0, W=0):
    '''
    Comments here
    '''
    if(GroupName is None):
        GroupName = 'HEXAPOD'
    if(CoordinateSystem is None):
        CoordinateSystem = 'Work'
    
    params = ','.join([GroupName, CoordinateSystem, 
                        str(X), str(Y), str(Z), str(U), str(V), str(W)])
    command_name = 'HexapodMoveAbsolute'
    cmd = command_name + '(' + params + ')'
    return cmd


def move_hexapod(fts):
    '''
    test function for moving hexapod
    '''
    x = 0
    y = 0
    z = -10
    u = 0
    v = 0
    w = 0

    generated_command = HexapodMoveAbsolute(X=x, Y=y, Z=z, U=u, V=v, W=w)
    err, msg = fts.newportxps._xps.Send(socketId = 0, cmd = generated_command)
    print(err, msg)

    return 

def main_2():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password', help='Password to connect to the NewportXPS')
    args = parser.parse_args()
    password = args.password
    fts = initialize_fts(password, num_sockets = 1, IP = '192.168.0.254')
    move_hexapod(fts)
    fts.close()



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

def FTS_calc_time(movement_params):
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

    movement_params['gather_time'] =  FTS_calc_time(movement_params) 
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
    fts = initialize_fts(password, num_sockets = 6, IP = '192.168.254.254')
    
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
    main_2()
    #graph_position_data('test_gather.dat')
  
    
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
        