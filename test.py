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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password', help='Password to connect to the NewportXPS')
    args = parser.parse_args()
    password = args.password

    fts = initialize_fts(password, num_sockets = 6)
    g1_min = -145
    g1_max = 145
    g2_min = -80
    g2_max = 120
    seq = write_seq(g1_min, g1_max, g2_min, g2_max)
    #seq = ['g2.-80', 'g1.-145', 'g1.145', 'g2.-40', 'g1.-145', 'g2.0', 'g1.145', 'g2.60', 'g1.-145', 'g2.120', 'g1.145', 'g2.-30', 'g1.0']
    #seq1 = [-145, 145, -145, 145]#, 10, 300, 8]
    #seq2 = [-120, 0, 110]#, 10, 300, 10, 400, 10]
    time_length = 120
    time_resolution = 0.2
    channel = 'ai0'
    channel2 = 'ai4'
    with ThreadPoolExecutor(max_workers=6) as executor:
        
        g = executor.submit(move_group, fts, seq, socket=0)
        #a = executor.submit(move_group1, fts,seq1 , socket=0)
        #b = executor.submit(move_group2, fts,seq2 , socket=1)
        c = executor.submit(read_positions, fts, 2, time_length, time_resolution, 'Group1')
        d = executor.submit(read_positions, fts, 3, time_length, time_resolution, 'Group2')
        e = executor.submit(nidaqmx_single_read, time_length, time_resolution, channel, 1)
        #f = executor.submit(nidaqmx_single_read, time_length, time_resolution, channel2, 1)
        nida_times, readings = e.result()
        nida_times2, readings2 = [],[]#f.result()
        pos1_times,pos1  = c.result()
        pos2_times,pos2 = d.result()
    
    plot_readings_timestamps(readings, nida_times,nida_times2, readings2,channel,channel2, pos1, pos1_times, pos2, pos2_times)
 

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