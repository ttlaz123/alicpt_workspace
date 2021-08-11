#!/usr/bin/env python

import sys
import os
import argparse
import ntplib
import time
import enum

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

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
from mynewportxps.newportxps import NewportXPS
from mynewportxps.newportxps.XPS_C8_drivers import XPSException
from mynewportxps.newportxps.newportxps import withConnectedXPS

class HexaChamber:
    def __init__(self):
        self.newportxps = None
    
    def initialize(self, host='192.168.0.254',username='Administrator',password='xxxxx',port=5001, timeout=100, kill_groups=True):
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

        default_velocity = 20.
    
        if (self.newportxps is None):     # Start a new connection
            try:
                self.newportxps = NewportXPS(host=host, username=username, password=password,port=port,timeout=timeout)
                print('STATUS: Connected to XPS')

            except Exception:
                print('ERROR: Cannot Connect to XPS')
                raise

        else:                           # From a reboot
            try:
                print('reboot')
                #self.newportxps.initialize()
                self.newportxps.connect()      # not tested
            except Exception:
                pass

        ### sometimes the groups are already initialized
        if(kill_groups):
            self.stop()
        self.newportxps.initialize_allgroups()
        print('STATUS: Initialized all groups')
        self.newportxps.home_allgroups()
        print('STATUS: Processed home search')

    def move_hexapod():
        return 