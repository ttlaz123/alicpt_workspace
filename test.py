import sys
import os
import argparse
import ntplib
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio
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


def nidaqmx_single_read(time_length, time_resolution, channel='ai1'):
    times = []
    readings = []
    n = 0
    voltage_channel = '/'.join(['Dev1', channel])
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(voltage_channel)
        time0 = time.time()
        time_elapsed = time.time()-time0 
        print(time_elapsed)
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
        print(time_start)
        print(time_end)
        times.append((time_start + time_end)/2)
        readings.append(x)
        time.sleep(time_resolution)
        n+=1
        time_elapsed = time.time()-time0 
    return times, readings


def plot_readings_timestamps(readings, timestamps, channel, pos, pos_times, pos2, pos_times2):
    utc_list = [datetime.utcfromtimestamp(t) for t in timestamps]
    utc_pos = [datetime.utcfromtimestamp(t) for t in pos_times]
    utc_pos2 = [datetime.utcfromtimestamp(t) for t in pos_times2]
    plt.plot(utc_list, [-r for r in readings], label='Voltage (V) in channel ' + str(channel))
    plt.plot(utc_pos, [p/100 for p in pos], label='group1 position/100')
    plt.plot(utc_pos2, [p/100 for p in pos2], label='group2 position/100')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Value')
    plt.legend()
    plt.show()

def initialize_fts(password, num_sockets):
    fts = AlicptFTS()
    varlist = []

    for i in ['Position', 'Velocity', 'Acceleration']:
        for j in ['Current', 'Setpoint']:
            for n in range(3):
                varlist.append('Group'+str(n)+'.Pos.'+j + i)

    x = fts.initialize('192.168.0.254','Administrator', password)
    print('***********************')
    print(x)
    for i in range(num_sockets):
        fts.newportxps.connect()
    print('Status: Finish initialization')
    fts.status()
    return fts

def move_group1(fts, pos, socket):
    for p in pos:
        fts.newportxps.move_stage(groupName['MovingLinear']+'.Pos', p ,False, socket=socket)
    return 

def move_group2(fts, pos, socket):
    for p in pos:
        fts.newportxps.move_stage(groupName['PointingLinear']+'.Pos', p ,False, socket=socket)
    return 

def get_pos1(fts, socket):
    pos = fts.newportxps.get_stage_position('Group1.Pos', socket=socket)
    return pos

def get_pos2(fts, socket):
    pos = fts.newportxps.get_stage_position('Group2.Pos', socket=socket)
    return pos

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password', help='Password to connect to the NewportXPS')
    args = parser.parse_args()
    password = args.password

    fts = initialize_fts(password, num_sockets = 6)
    print('done initializing')
    time.sleep(5)    
    move_group1(fts, [10, 50], socket=0)
    print('finished moving group 1')
    time.sleep(5)
    seq1 = [60, 30, 200]#, 10, 300, 8]
    seq2 = [100, 10,  150]#, 10, 300, 10, 400, 10]
    time_length = 20
    time_resolution = 0.002
    with ThreadPoolExecutor(max_workers=5) as executor:
        
        a = executor.submit(move_group1, fts,seq1 , socket=0)
        b = executor.submit(move_group2, fts,seq2 , socket=1)
        c = executor.submit(read_positions, fts, 2, time_length, time_resolution, 'Group1')
        d = executor.submit(read_positions, fts, 3, time_length, time_resolution, 'Group2')
        e = executor.submit(nidaqmx_single_read, time_length, time_resolution)
        nida_times, readings = e.result()
        pos1_times,pos1  = c.result()
        pos2_times,pos2 = d.result()
    channel = 'ai0'
    plot_readings_timestamps(readings, nida_times,channel, pos1, pos1_times, pos2, pos2_times)
 

if __name__ == '__main__':
    main()
  
    
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