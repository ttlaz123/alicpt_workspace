import sys
from enum import Enum
import os

projpath = os.getcwd()
projpath = projpath.split('alicptfts')[0] + 'alicptfts'

sys.path.append(projpath+'\lib')
#sys.path.append(projpath)

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
import System
import os
import time
from collections import OrderedDict
from configparser import ConfigParser
from time import sleep
#from sftpwrapper import SFTPWrapper
#import sftpwrapper

# import pythonnet
from System import  Array
from System.Collections import *
clr.AddReference(r'Newport.XPS.CommandInterface')
from CommandInterfaceXPS import *
import numpy as np

print('Loading assembly')

# reference code: XPS Unified Programmer's Manual.pdf, p9
myXPS = XPS()

# op = myXPS.OpenInstrument(host, port,timeout)
hostIP = '192.168.0.254'
op = myXPS.OpenInstrument(hostIP, 5001, 1000)
if (op != 0): raise ValueError('Error: Could not open XPS for test\nError code: {}'.format(op))
else: print("Status: connecting to the XPS controller")

# reference code: XPS Unified Programmer's Manual.pdf, Ch.9
op = myXPS.Login('Administrator','Administrator','DUMMY') ## not sure whether it's required
if (op[0] != 0): raise ValueError('Error: Could not login\nError code: {}'.format(op))
else: print("Status: Login XPS")

op = myXPS.KillAll('DUMMY')
if (op[0] != 0): raise ValueError('Error: Could not reset group status\nError code: {}'.format(op))
else: print("Status: Reset All Groups")

# group: XPS Unified Programmer's Manual.pdf, Ch.5
groupName = 'Group1'  # linear motor

op = myXPS.GroupInitialize(groupName,'DUMMY')
if (op[0] != 0): raise ValueError('Error: Could not initialize group\nError code: {}'.format(op))
else: print('Status: Initialize group')

sleep(1)

op = myXPS.GroupHomeSearch(groupName,'DUMMY')
if (op[0] != 0): raise ValueError('Error: Could not search home group\nError code: {}'.format(op))
else: print('Status: Search home group')

pos1 = Array[float]([0,0])
op = myXPS.GroupMoveAbsolute(groupName,pos1,1,'DUMMY')
if (op[0] != 0): raise ValueError('GroupMoveAbsolute Error\nError code: {}'.format(op))
else: print('Status: Reset the position to origin')

sleep(1)

pos2 = Array[float]([100,0])
op = myXPS.GroupMoveRelative(groupName,pos2,1,'DUMMY')
if (op[0] != 0): raise ValueError('GroupMoveRelative Error\nError code: {}'.format(op))
else: print('Status: move to +100 mm')

op = myXPS.CloseInstrument()
if (op[0] != 0): raise ValueError('Error: Failure to close XPS\nError code: {}'.format(op))
else: print('Status: Close Connection\nTest Finish')