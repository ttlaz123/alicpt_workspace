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

import posixpath
print(" Current directory: " + str(os.getcwd()))
# import System
# from System import String

sys.path.append(r'.')
sys.path.append(r'lib')
sys.path.append(r'..')

# import lib.MC2000B_COMMAND_LIB as mc2000b
# import MC2000B_COMMAND_LIB as mc2000b
from mynewportxps.newportxps import NewportXPS
from mynewportxps.newportxps.XPS_C8_drivers import XPSException
from mynewportxps.newportxps.newportxps import withConnectedXPS


class FTSState(enum.Enum):
    NOTINIT  = 0
    INIT     = 1
    CONFIG   = 2
    SCANNING = 3
    PAUSE    = 4
    FINISH   = 5

class FTSmotion(enum.Enum):
    PointingLinear = 0
    PointingRotary = 1
    MovingLinear = 2

groupName = {'PointingLinear': 'Group2',
    'PointingRotary': 'Group3',
    'MovingLinear': 'Group1'}

class MC2000B:
    def __init__(self):
        pass

class IR518:
    def __init__(self):
        pass

class AlicptFTS:
    HOME = (8, 0)
    def __init__(self):
        self.source = None
        self.chopper = None
        self.newportxps = None 
        self.config = AlicptFTS.HOME
        self.state = FTSState.NOTINIT
        self.ntpObj = None

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
        self.check_state('initialize')
        
        # Current implementation considers only the XPS controller
        self.source = IR518()
        self.chopper = MC2000B()
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
        self.state = FTSState.INIT
        


    def configure(self, position, angle, relative=False):
        """Configure the stages so that the FTS is ready to scan.
        
        One my wish to modify the motion params before configuring
        the pointing mirror. In that case, call the set_motion_params
        function, e.g.,
        self.set_motion_params('PointingLinear', params_lin)
        self.set_motion_params('PointingRotary', params_rot)

        Parameters
        ----------
        position : float
            Target coordinates of the pointing mirror in (position, angle).

        angle : array of float
            Target coordinates of the pointing mirror in (position, angle).

        relative : bool
            If relative is True, the pointing mirror is configured to the
            original coordinates plus "positions" (default is False).
        """
        self.check_state('configure')
        try:
            # self.newportxps.move_stage(groupName[MovingLinear]+'.Pos',0 ,relative)
            self.newportxps.move_stage(groupName['PointingLinear']+'.Pos',position,relative)
            self.newportxps.move_stage(groupName['PointingRotary']+'.Pos',angle,relative)
            if(relative):
                self.config = (position + self.config[0], angle + self.config[1])
            else:
                self.config = (position, angle)
        except Exception:
            pass

        self.state = FTSState.CONFIG

    def set_trigger_start(fts, groupname, socket=0, verbose=False):
        """
        TODO write function string
        """
        trigger = 'SGamma.MotionStart'
        event_name = '.'.join([groupname, trigger])
        err, ret = fts.newportxps._xps.EventExtendedConfigurationTriggerSet(socket, [event_name], ['0'],['0'],['0'],['0'])
        fts.newportxps.check_error(err, msg='EventConfigTrigger')
        if verbose:
            print( " EventExtended Trigger Set ", ret)
        return 

    def configure_gathering_time(self, run_time, collection_resolution, socket=0, verbose=False):
        """
        TODO: Write function string
        """
        action_name = 'GatheringRun'
        milli_to_sec = 1000 # 1000 milliseconds in a second
        run = int(run_time * milli_to_sec) 
        milli_to_servo = 10000 # each servo cycle is 1/8000 sec
        servo_cycle = int(collection_resolution * milli_to_servo)

        err, ret = self.newportxps._xps.EventExtendedConfigurationActionSet(socket, [action_name], 
                                                    [str(run)], [str(servo_cycle)], ['0'], ['0'])
        self.newportxps.check_error(err, msg='GatherConfigSet')
        if verbose:
            print( " Gather Run Set: " + str( ret))
        return 

    def gather_data_setup(self, gather_time, gather_resolution, gather_params, socket=0):
        """
        TODO: write function string

        Assumes trigger is movement of first group in gather_params
        TODO: other trigger functions
        """

        ### TODO this should probably be an input intead of coded up in here
        start_group = gather_params[0]
        tlist = start_group.split('.')
        trigger_start_group = '.'.join(tlist[:2])
        print(trigger_start_group)

        self.newportxps._xps.GatheringConfigurationSet(socket, gather_params)
        self.set_trigger_start(trigger_start_group, verbose=True)
        self.configure_gathering_time(gather_time, gather_resolution, verbose=True)
        eventID, m = self.newportxps._xps.EventExtendedStart(socket)
        return eventID, trigger_start_group 

    def gather_end_and_save(self, gather_filename, headers, eventID, socket=0):
        """
        TODO: write function string
        """

        ret = self.newportxps._xps.EventExtendedRemove(socket, eventID)
        ret = self.newportxps._xps.GatheringStopAndSave(socket)
        
        self.read_and_save(gather_filename, headers)

    def generate_headers(self, scan_params, time_start, time_end):
        """
        TODO: write function string
        """
        headers = []
        timestamp = "Time start %f, Time end %f, Time diff %f" % (time_start, time_end, time_end-time_start)
        headers.append(timestamp)
        headers.append(";".join(scan_params))
        return headers

    def perform_movement(self, trigger_start_group, scan_range, repeat, velocity=200, accel=600, socket=0):
        """
        TODO: write function string
        """
        self.newportxps.set_velocity(trigger_start_group, velocity,accel)
        time_start = time.time()
        for i in range(repeat):
            self.newportxps.move_stage(trigger_start_group, scan_range[0])
            self.newportxps.move_stage(trigger_start_group, scan_range[1])
        self.newportxps.move_stage(trigger_start_group, scan_range[0])
        time_end = time.time()
        return time_start, time_end

    def scan(self, configure=None, scan_params=None, scan_range=None, repeat=5, velocity=200, accel=600, filename=None):
        """Perform a scan with the configured stages.
        
        Parameters
        ----------
        scan_params : array of float, optional
            Scan parameters for the SGamma profile (see Newport XPS-D
            feature manual pp. 8-9). Use format
            [vel, acc, min_jerk_time, max_jerk_time]. Simply put the not-
            interested parameters as "None". In that case, the default
            value (or value set by an previous operation) will be used.
            Will use default values if not specificed (None).
    
        scan_range : array of float, optional
            Minimum and maximum target positions. Use format 
            [min_target, max_target].
            Will use default values if not specified (None).

        repeat : int
            Number of full back-and-forth scans (default is 15).
        """
        self.check_state('scan')
        '''
        #self.newportxps._xps.('scan_test.dat')
        #print()
        if (scan_params): 
            self.newportxps._xps.GatheringConfigurationSet(self.newportxps._sid,scan_params)
        else: 
            raise XPSException('ERROR: Cannot set gathering data')
        #print('Function Status: set data gathering')
        '''
        if(scan_params is None):
            ## TODO put function in class
            scan_params = generate_scanparams()
        if(scan_range is None):
            ## TODO acquire this from newportxps instead of hardcode
            min_range = 0
            max_range = 500
            scan_range = [min_range, max_range]
        if(configure is not None):
            self.configure(configure[0], configure[1])
        else:
            configure = self.config
        gather_time = 20 #self.calculate_gather_time()
        gather_resolution = 0.001
        event_ID, trigger_start_group = self.gather_data_setup(gather_time, gather_resolution, scan_params)
        time_start, time_end = self.perform_movement(trigger_start_group, scan_range, repeat, velocity=velocity, accel=accel)
        #self.newportxps.move_stage('Group1.Pos', 200, True)
        if(filename is None):
            filename = 'scan_range_%d_%d__configure_%d_%d.dat' % (scan_range[0], scan_range[1], configure[0], configure[1])
        headers = self.generate_headers(scan_params, time_start, time_end)
        self.gather_end_and_save(filename, headers, event_ID)
        '''
        
        self.newportxps.move_stage('Group1.Pos', 50.)
        ## self.newportxps.GatheringReset(self.newportxps._sid)
        #print('Function Status: GatheringRun')
        #self.newportxps._xps.GatheringRun(self.newportxps._sid, len(scan_params)*10000, 8) ## max 1M
        self.newportxps.move_stage('Group1.Pos', 200.,True)
        print('Function Status: GatheringStop')
        self.newportxps._xps.GatheringStop(self.newportxps._sid)

        print('Function Status: GatheringStopAndSave')
        #err, mes = self.newportxps._xps.GatheringStopAndSave(self.newportxps._sid)
        print('Function Status: Finished GatheringStopAndSave')
        #print(err)
        #print(mes)

        print('Function Status: Save output')

        try:
            self.read_and_save('newGathering.dat', [])
            #self.set_motion_params('MovingLinear', scan_params)

        except:
            print('Warning: Cannot download data')
            print('Please look for data on XPS')
            raise

        
        self.state = FTSState.SCANNING
        try:
            timestamps = self.newportxps.scan(scan_range=scan_range, repeat=repeat)
        except XPSException:
            pass
        except Exception:
            self.state = FTSState.NOTINIT
            pass
        else:
            self.state = FTSState.FINISH
            return timestamps
        
        '''
    def scan_event(self, scan_params=None, scan_range=None, repeat=15):
        self.check_state('scan')
        #self.newportxps._xps.('scan_test.dat')
        print()

        self.newportxps.GatheringReset(self.newportxps._sid)
        if (scan_params): self.newportxps._xps.GatheringConfigurationSet(self.newportxps._sid,scan_params)
        else: raise XPSException('ERROR: Cannot set gathering data')
        print('Function Status: set data gathering')

        self.newportxps.move_stage('Group1.Pos', 50.)
        print('Function Status: set event trigger')
        self.newportxps._xps.EventExtendedConfigurationTriggerSet(self.newportxps._sid,['Group1.Pos.SGamma.MotionStart'],0,0,0,0)
        print('Function Status: set event action')
        self.newportxps._xps.EventExtendedConfigurationActionSet(self.newportxps._sid,['GatheringRun'], 10000, 8, 0, 0)
        #self.newportxps._xps.GatheringRun(self.newportxps._sid, len(scan_params)*10000, 8) ## max 1M
        print('Function Status: event start')
        self.newportxps._xps.EventExtendedStart(self.newportxps._sid)
        self.newportxps.move_stage('Group1.Pos', 200.,True)
        print('Function Status: GatheringStop')
        self.newportxps._xps.GatheringStop(self.newportxps._sid)
        print('Function Status: GatheringStopAndSave')
        err, mes = self.newportxps._xps.GatheringStopAndSave(self.newportxps._sid)
        print('Function Status: Finished GatheringStopAndSave')
        print(err)
        print(mes)
        print('Function Status: GatheringCurrentNumberGet, ', self.newportxps._xps.GatheringCurrentNumberGet(self.newportxps._sid))

        try:
            print('Function Status: Save output')
            self.newportxps.read_and_save('newGathering_event.dat')
            print('nGathering: ', self.newportxps.ngathered)
            #self.set_motion_params('MovingLinear', scan_params)

        except:
            print('Warning: Cannot download data')
            print('Please look for data on XPS')



    def save(self, timestamps=None, tname='TIMESTAMPS.DAT', fname='GATHERING.DAT'):
        """Save the gathering data and timestamps after a scan.

        Parameters
        ----------
        timestamps: array of float
            Timestamps for data points reported by the "scan()" 
            function. If None, then no timestamps will be saved.

        tname: string
            Name of the file storing the timestamps (default is
            'TIMESTAMPS.DAT'). Can specify absolute path.

        fname: string
            Name of the file storing the gathering data, including
            encoder positions and velocities (default is 
            'GATHEIRNG.DAT'). Can specify absolute path.
        """
        self.check_state('save')
        try:
            self.newportxps.save_gathering(fname)
        except Exception:
            pass

        if timestamps is not None:
            try:
                self.save_timestamps(timestamps, tname)
            except Exception:
                pass

    def download_data(self, filename=None):
        """download text of data file on newport XPS
        Arguments:
        ----------
           filename  (str):   data file name. Default 'Public/Gathering.dat'
        """
        if (filename is None): filename = ['Public','Gathering.dat']
        elif (type(filename) is str): filename = [filename]
        elif (type(filename) is list): pass
        else: raise TypeError('Require the file path (\'Public/Gathering.dat\')')

        self.newportxps.ftpconn.connect(**self.newportxps.ftpargs)
        remote_path = posixpath.join(self.newportxps.ftphome, *filename)
        self.newportxps.ftpconn.cwd(remote_path)
        self.newportxps.ftpconn.save(posixpath.basename(remote_path), posixpath.basename(remote_path))
        self.newportxps.ftpconn.close()

    def reboot(self):
        """Reboot the system to the NOTINIT state"""
        self.check_state('reboot')
        try:
            self.newportxps.reboot(reconnect=False, timeout=120.0)
        except Exception:
            pass

    def stop(self):
        """Abort any ongoing motions
        
        Bring the system back to the NOTINIT state. Applicable when
        the system is in the CONFIG or the SCANNING states.
        """
        self.check_state('stop')
        try:
            #self.newportxps.stop_all()
            self.newportxps._xps.KillAll(self.newportxps._sid)
        except Exception:
            pass
    
    def pause(self):
        """Temporarily hold the system from further actions
        
        Applicable when the system is in the CONFIG state.
        """
        self.check_state('pause')
        try:
            self.newportxps.abort_group('Group1')  # Group name is not determined
        except Exception:
            pass

    def resume(self):
        """Bring the paused system back to the CONFIG state"""
        self.check_state('resume')
        try:
            self.newportxps.resume_all()
        except Exception:
            pass

    def status(self):
        try:
            self.check_state('status')
        except Exception:
            pass
        try:
            status_report = self.newportxps.status_report()
            print(status_report)
        except Exception:
            pass

    def close(self):
        """Close the instrument (socket of the XPS)"""
        try:
            self.check_state('close')
        except Exception:
            pass
        try:             # copy from reboot function
            self.newportxps.ftpconn.close()
            self.newportxps._xps.CloseAllOtherSockets(self.newportxps._sid)
        except Exception:
            pass

    def get_network_time(self):
        NTPserver = ['pool.ntp.org', 'time.stanford.edu']
        if (self.ntpObj is None): self.ntpObj = ntplib.NTPClient()
        ntpResponse = 0
        for server in NTPserver:
            try:
                ntpResponse = self.ntpObj.request(server)
                # print('NTP SERVER: ' + server)
                break
            except:
                pass

        if (ntpResponse):
            return ntpResponse.tx_time
        else:
            return None

    def get_time_diff(self):

        ntpResponse = self.get_network_time()
        if (ntpResponse):
            diff = time.time() - ntpResponse
            return diff

        else:
            ## warnings.warn(message, category=None, stacklevel=1, source=None)
            print('Warning: CANNOT Get NTP Time.')
            print('Using Local Time.')
            return 0

    ## Helper functions
    def save_timestamps(self, timestamps, tname):
        try:
            print('Do Nothing')
            #np.savetxt(tname, np.array(timestamps), delimiter=' ')
        except FileNotFoundError:
            print('ERROR: cannot find the output file')
            raise


    def set_motion_params(self, xps_grp, params):
        """Set the SGamma profile parameters for an XPS positioner
        
        Parameters
        ----------
        xps_grp : string
            One of the following: PointingLinear, PointingRotary,
            and MovingLinear.

        params : array of float
            Scan parameters for the SGamma profile in
            [vel, acc, min_jerk_time, max_jerk_time]. Simply put the not-
            interested parameters as "None".
            Will use default values if not specificed (None).
        """

        # if (xps_grp not in groupName): raise KeyError("KeyError: '{}' is not in ".format(xps_grp))
        if (xps_grp not in groupName): raise KeyError(xps_grp)

        temp_par = [None]*4
        if (type(params) is int or type(params) is float): temp_par[0] = float(params)
        elif (type(params) is list):
            if (len(params) > 0):
                for i,par in enumerate(params):
                    if (i>=4): break
                    temp_par[i] = par
            else: temp_par[0] = 20.  ## Set velocity with default value

        else:
            raise TypeError('ERROR: Require a list or float for parameters')

      
        self.newportxps.set_velocity(groupName[xps_grp]+'.Pos',
                                     velo=temp_par[0], accl=temp_par[1],
                                     min_jerktime=temp_par[2], max_jerktime=temp_par[3])
    

    
    def determine_num_chunks(self, total_lines, socket=0, max_entries=5000):
        """Determines the number of chunks to breakup the Gathering.dat file
            to be able to read into python
        
        Parameters
        ----------
        total_lines : int
            number of total lines in the Gathering.dat file

        socket : int
            the xps socket to connect to in order to execute this command
        
        max_lines : int
            maximum number of entries to read in per chunk

        Returns 
        -----------
        nchunks : int
            number of chunks to break up Gathering.dat
        """
        
        ret, msg = self.newportxps._xps.GatheringDataMultipleLinesGet(socket, 0, 1)
        num_entries = len(msg.split(';'))
        print(num_entries)
        max_lines = max_entries / num_entries
        nchunks = int(total_lines/max_lines)+1
        num_lines = total_lines 
        success = False
        while(not success):
            print('Current number of chunks ' + str(nchunks))
            ret, _ = self.newportxps._xps.GatheringDataMultipleLinesGet(socket, 0, int(num_lines))
            print('Current number of lines ' + str(num_lines))
            if(ret < 0):
                nchunks *= 1.5
                num_lines = total_lines/nchunks 
                
            else:
                print('Success')
                success = True 
            
            if(num_lines < 10):
                raise AttributeError('XPS not reading even though small enough chunks')
        return int(nchunks) 

    def read_and_save(self, filename, headers, socket=0):
        """Reads the Gathering.dat file on the XPS machine and saves it 
            to filename
        
        Parameters
        ----------
        filename : str
            path/to/location of file for saving the Gathering.dat info

        headers : list of str
            A list of headers to write on top of the file. Each item in the list
            will be a separate line
        
        socket : int
            the xps socket to connect to in order to execute this command

        Returns 
        -----------
        None
        """
        
        ret, total_lines, max_lines = self.newportxps._xps.GatheringCurrentNumberGet(socket)
        nchunks = self.determine_num_chunks(total_lines, socket)
        print('Number of chunks: ' + str(nchunks))
        lines_per_chunk = int(total_lines/nchunks)
        remaining_lines = total_lines - lines_per_chunk*nchunks
        with open(filename, 'w') as f:
            for header in headers:
                f.write("## " + header + "\n")
            for i in range(nchunks):
                start = lines_per_chunk*i 
                ret, buffer = self.newportxps._xps.GatheringDataMultipleLinesGet(socket, start, lines_per_chunk)
                f.write(buffer)
            start = lines_per_chunk * nchunks
            ret, buffer = self.newportxps._xps.GatheringDataMultipleLinesGet(socket, start, remaining_lines)
            f.write(buffer)
        return 
    
    
    ## TODO
    def check_state(self, command):
        if command == 'initialize': pass
        elif command == 'configure': pass
        elif command == 'scan': pass
        elif command == 'save': pass
        elif command == 'reboot': pass
        elif command == 'stop': pass
        elif command == 'pause': pass
        elif command == 'resume': pass
        elif command == 'status': pass
        elif command == 'close': pass
        else:
            print('Error: Invalid command', command)
            #raise ValueError('Error: Invalid command')

def generate_scanparams(num_groups=3, 
                    param_list = ['Position', 'Velocity', 'Acceleration'],
                    point_types = ['Current', 'Setpoint']):
    varlist = []

    for i in param_list:
        for j in point_types:
            for n in range(1, num_groups+1):
                varlist.append('Group'+str(n)+'.Pos.'+j + i)

    return varlist

def old_main():
    fts = AlicptFTS()
    varlist = []

    for i in ['Position', 'Velocity', 'Acceleration']:
        for j in ['Current', 'Setpoint']:
            for n in range(3):
                varlist.append('Group'+str(n)+'.Pos.'+j + i)

    fts.initialize('192.168.254.254','Administrator','xxxxxxxx')
    print('Status: Finish initialization')
    fts.status()
    fts.configure(50,0)
    print('Status: Set configure')
    ##################
    ## test 1
    fts.scan(varlist)
    ##################
    ## test 2
    # fts.scan_event(varlist)
    ##################
    print('Status: Scan Test Finished')
    print('PASS TESTS')
    print('Disconnect...')
    fts.close()
    print('Done')

    '''
    fts = AlicptFTS()
    fts.initialize()
    fts.status()
    fts.configure(positions=[50.0, 35.0], relative=False)
    timestamps = fts.scan()
    fts.save(timestamps=timestamps)
    fts.close()
    '''

def test_function(fts):
    scan_params = generate_scanparams(param_list=['Position'], point_types=['Setpoint'])
    print(scan_params)

    default_velocity1 = 20.
    default_velocity2 = 20.
    default_velocity3 = 20.
    fts.set_motion_params('MovingLinear',[default_velocity1])
    fts.set_motion_params('PointingRotary', [default_velocity3])
    fts.set_motion_params('PointingLinear', [default_velocity2])
    print('STATUS: Done setting motion parameters')

    print('************ scanning params ******************')
    fts.scan(scan_params=scan_params, configure=(30, 5), scan_range=(20, 80), repeat=3)
    fts.scan(scan_params=scan_params, configure=(300, 50), scan_range=(20, 80), repeat=3)
    fts.scan(scan_params=scan_params, configure=(60, 35), scan_range=(20, 80), repeat=3)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password', help='Password to connect to the NewportXPS',
                        default="password")
    parser.add_argument('-a', '--ip_address', help="ip address of newport xps machine", 
                        default='192.168.254.254')
    args = parser.parse_args()
    
    password = args.password
    ip = args.ip_address
    user = 'Administrator'

    fts = AlicptFTS()

    fts.initialize(ip, user, password)
    test_function(fts)
    fts.close()


if __name__ == '__main__':
    main()
