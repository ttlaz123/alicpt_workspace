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
        