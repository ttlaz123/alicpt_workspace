"""
Written by Tom Liu, 2021 Aug 11
Much of this code is imported from newportxps.py, revamped for hexapod chamber use
This was a rush job, so apologies for the lack of commenting
"""
#!/usr/bin/env python

import sys
import os
import argparse
import ntplib
import time
import enum
import socket

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor

print(" Current directory: " + str(os.getcwd()))
# import System
# from System import String

sys.path.append(r'.')
sys.path.append(r'lib')
sys.path.append(r'..')
sys.path.append(r'../alicptfts')
sys.path.append(r'../alicptfts/alicptfts')

# import lib.MC2000B_COMMAND_LIB as mc2000b
# import MC2000B_COMMAND_LIB as mc2000b
from mynewportxps.newportxps.XPS_C8_drivers import XPS, XPSException
from mynewportxps.newportxps.ftp_wrapper import SFTPWrapper, FTPWrapper
from mynewportxps.newportxps import NewportXPS
from alicptfts.alicptfts import AlicptFTS



class HexaChamber:
    def __init__(self, host, group=None,
                 username='Administrator', password='xxxxxx', groupname='HEXAPOD',
                 port=5001, timeout=10, extra_triggers=0, xps=None):

        """Establish connection with each part.
        
        Parameters
        ----------
        host : string
            IP address of the XPS controller.

        port : int
            Port number of the XPS controller (default is 5001).

        timeout : int
            Receive timeout of the XPS in milliseconds 
            (default is 1000). Note that the send timeout is 
            set to 1000 milliseconds. See the XPS Programming 
            Manual.

        username : string (default is Administrator)

        password : string (default is Administrator)
        """
        socket.setdefaulttimeout(5.0)
        try:
            host = socket.gethostbyname(host)
        except:
            raise ValueError('Could not resolve XPS name %s' % host)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.groupname = groupname
        self.extra_triggers = extra_triggers

        self.firmware_version = None

        self.ftpconn = None
        self.ftpargs = dict(host=self.host,
                            username=self.username,
                            password=self.password)
        self.sid = None
        if(xps is None):
            self.xps = XPS()
        else:
            self.xps = xps
        self.sid = self.connect()
    
    def initialize(self, kill_groups=True):
        """Initialize the Hexapod
        
        Parameters
        ----------
        GroupName
        kill_groups
        """
        ### sometimes the groups are already initialized
        if(kill_groups):
            self.xps.KillAll(socketId=None)
        self.xps.GroupInitialize(socketId=None, GroupName=self.groupname)
        print('STATUS: Initialized all groups')
        self.xps.GroupHomeSearch(socketId=None, GroupName=self.groupname)
        print('STATUS: Processed home search')



    def check_error(self, err, msg='', with_raise=True):
        if err != 0:
            err = "%d" % err
            desc = self.xps.errorcodes.get(err, 'unknown error')
            print("XPSError: message= %s, error=%s, description=%s" % (msg, err, desc))
            if with_raise:
                raise XPSException("%s %s [Error %s]" % (msg, desc, err))

    def connect(self):
        self.sid = self.xps.TCP_ConnectToServer(self.host,
                                                  self.port, self.timeout)
        print('Socked ID:' + str(self.sid))
        print('Begin Login')
        try:
            
            err, val = self.xps.Login(self.sid, self.username, self.password)
            passwordError = -106
            if(int(err) == passwordError ):
                raise XPSException('Incorrect Password: ' + str(err))
            
        except:
            raise XPSException('Login failed for %s and password %s' % (self.host, self.password))
        
        err, val = self.xps.FirmwareVersionGet(self.sid)
        self.firmware_version = val
        self.ftphome = ''

        if 'XPS-D' in self.firmware_version:
            err, val = self.xps.Send(self.sid, 'InstallerVersionGet(char *)')
            self.firmware_version = val
            self.ftpconn = SFTPWrapper(**self.ftpargs)
        else:
            self.ftpconn = FTPWrapper(**self.ftpargs)
            if 'XPS-C' in self.firmware_version:
                self.ftphome = '/Admin'
        return self.sid

    
    def HexapodMoveAbsoluteCmd(self, GroupName=None, CoordinateSystem=None, 
                            X=0, Y=0, Z=0, U=0, V=0, W=0):
        '''
        Comments here
        '''
        if(GroupName is None):
            GroupName = self.groupname
        if(CoordinateSystem is None):
            CoordinateSystem = 'Work'
        
        params = ','.join([GroupName, CoordinateSystem, 
                            str(X), str(Y), str(Z), str(U), str(V), str(W)])
        command_name = 'HexapodMoveAbsolute'
        cmd = command_name + '(' + params + ')'
        return cmd

    def HexapodMoveIncrementalCmd(self, GroupName=None, CoordinateSystem=None, 
                            dX=0, dY=0, dZ=0, dU=0, dV=0, dW=0):
        '''
        Comments here
        '''
        if(GroupName is None):
            GroupName = self.groupname
        if(CoordinateSystem is None):
            CoordinateSystem = 'Work'
        
        params = ','.join([GroupName, CoordinateSystem, 
                            str(dX), str(dY), str(dZ), str(dU), str(dV), str(dW)])
        command_name = 'HexapodMoveIncremental'
        cmd = command_name + '(' + params + ')'
        return cmd 
    
    def incremental_move(self, coord_sys=None, dX=0, dY=0, dZ=0, dU=0, dV=0, dW=0):
        '''
        performs the actual movement
        '''
        generated_command = self.HexapodMoveIncrementalCmd(CoordinateSystem=coord_sys,
                                    dX=dX, dY=dY, dZ=dZ, dU=dU, dV=dV, dW=dW)

        print('Socket: ' + str(self.sid))
        err, msg = self.xps.Send(socketId=self.sid, cmd = generated_command)
        return err, msg
    
    def close(self):
        """Close the instrument (socket of the XPS)"""
        try:
            self.check_state('close')
        except Exception:
            pass
        try:             # copy from reboot function
            self.ftpconn.close()
            self.xps.CloseAllOtherSockets(self.sid)
        except Exception:
            pass


 
def close_positioner(positioner):
    positioner.ftpconn.close()
    positioner.xps.CloseAllOtherSockets()

def initialize_hexapod(password, IP, username='Administrator', xps=None, reinitialize=False):
    """
    does the initiazliing stuff
    TODO: add comments
    """
    print('Initializing Hexapod')
    
    hex = HexaChamber(host=IP, username=username, password=password, xps=xps)
    if(reinitialize):
        hex.initialize()
    print('STATUS: Finished Initialization')
    return hex

def initialize_positioner(password, IP, username='Administrator'):
    """
    does the initiazliing stuff
    TODO: add comments
    """
    print('Initializing Hexapod')
    
    pos = NewportXPS(host=IP, username=username, password=password)

    Groupname = 'Group3'
    print(pos._xps.KillAll(socketId=None))
    print(pos._xps.GroupInitialize(socketId=None, GroupName=Groupname))
    print('STATUS: Initialized all groups')
    print(pos._xps.GroupHomeSearch(socketId=None, GroupName=Groupname))
    print('STATUS: Processed home search')
    print('STATUS: Finished Initialization')
    return pos

def move_hexapod_test(hex, pos):
    '''
    test function for moving hexapod
    '''

    print('moving pos')
    print('socket' + str(pos._sid))
    print(pos.move_stage(stage='Group3.Pos', value=10, relative=True))
    
    print('moving dz')
    print(hex.incremental_move(dZ=3))
    
    print('moving dx')
    print(hex.incremental_move(dX=1))

    print('moving pos')
    print('socket' + str(pos._sid))
    print(pos.move_stage(stage='Group3.Pos', value=-5, relative=True))


    print('moving dz')
    print(hex.incremental_move(dZ=1))
    print('moving dx')
    print(hex.incremental_move(dX=-1))
    print('moving du')

    print('moving pos')
    print('socket' + str(pos._sid))
    print(pos.move_stage(stage='Group3.Pos', value=-5, relative=True))

    print(hex.incremental_move(dU=3))
    print('moving du dz')
    print(hex.incremental_move(dU=-3, dZ=-1))
    print('moving dw dz')
    print(hex.incremental_move(dW=5, dZ=-1))

    return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--hex_ip', default='192.168.0.254',
                    help='IP address to connect to the NewportXPS hexapod')
    parser.add_argument('-j', '--pos_ip', default='192.168.254.254',
                    help='IP address to connect to the NewportXPS positioner')
    parser.add_argument('-p', '--hex_password', help='Password to connect to the NewportXPS hexapod')
    parser.add_argument('-q', '--pos_password', help='Password to connect to the NewportXPS positioner' )
    args = parser.parse_args()

    password = args.pos_password
    IP = args.pos_ip
    positioner = initialize_positioner(password, IP = IP)

    password = args.hex_password
    IP = args.hex_ip
    hexapod = initialize_hexapod(password, IP = IP, xps=positioner._xps, reinitialize=True)

    
    

    

    move_hexapod_test(hexapod, positioner)
    hexapod.close()

if __name__ == '__main__':
    main()