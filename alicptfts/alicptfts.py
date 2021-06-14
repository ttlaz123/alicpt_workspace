#!/usr/bin/env python

import sys
import os
import ntplib
import time

print(os.getcwd())
# import System
# from System import String

sys.path.append(r'../lib')
sys.path.append(r'lib')
sys.path.append(r'..')
sys.path.append(r'.')


# import lib.MC2000B_COMMAND_LIB as mc2000b
# import MC2000B_COMMAND_LIB as mc2000b
#from mynewportxps import NewportXPS
from mynewportxps.newportxps import NewportXPS
from mynewportxps.newportxps.XPS_C8_drivers import XPSException
#from mynewportxps.newportxps.XPS_C8_drivers import XPSException
from mynewportxps.newportxps.newportxps import withConnectedXPS
import posixpath

import enum


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
    def __init__(self):
        self.source = None
        self.chopper = None
        self.newportxps = None 
        self.state = FTSState.NOTINIT
        self.ntpObj = None

    def initialize(self, host='192.168.0.254',username='Administrator',password='xxxxxxxx',port=5001, timeout=100):
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
        print('****************************')
        self.stop()
        self.newportxps.initialize_allgroups()
        print('STATUS: Initialized all groups')
        self.newportxps.home_allgroups()
        print('STATUS: Processed home search')
        self.state = FTSState.INIT
        self.set_motion_params('MovingLinear',[20.])
        self.set_motion_params('PointingRotary', [20.])
        self.set_motion_params('PointingLinear', [20.])


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

        except Exception:
            pass

        self.state = FTSState.CONFIG

    def scan(self, scan_params=None, scan_range=None, repeat=15):
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
        #self.newportxps._xps.('scan_test.dat')
        #print()
        if (scan_params): self.newportxps._xps.GatheringConfigurationSet(self.newportxps._sid,scan_params)
        else: raise XPSException('ERROR: Cannot set gathering data')
        #print('Function Status: set data gathering')


        self.newportxps.move_stage('Group1.Pos', 50.)
        ## self.newportxps.GatheringReset(self.newportxps._sid)
        #print('Function Status: GatheringRun')
        self.newportxps._xps.GatheringRun(self.newportxps._sid, len(scan_params)*10000, 8) ## max 1M
        self.newportxps.move_stage('Group1.Pos', 200.,True)
        print('Function Status: GatheringStop')
        self.newportxps._xps.GatheringStop(self.newportxps._sid)

        print('*******************************')
        print('Function Status: GatheringStopAndSave')
        err, mes = self.newportxps._xps.GatheringStopAndSave(self.newportxps._sid)
        print('Function Status: Finished GatheringStopAndSave')
        print(err)
        print(mes)

        print('Function Status: Save output')

        try:
            self.newportxps.read_and_save('newGathering.dat')
            #self.set_motion_params('MovingLinear', scan_params)

        except:
            print('Warning: Cannot download data')
            print('Please look for data on XPS')
            raise

        '''
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
        #try:
        print('stopping')
        #self.newportxps.stop_all()
        self.newportxps._xps.KillAll(self.newportxps._sid)
        '''
            except Exception:
            print('Error')
            pass
        '''
    
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

        try:
            self.newportxps.set_velocity(groupName[xps_grp]+'.Pos',
                                     velo=temp_par[0], accl=temp_par[1],
                                     min_jerktime=temp_par[2], max_jerktime=temp_par[3])
        except Exception:
            pass

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

import matplotlib.pyplot as plt
def main():
    fts = AlicptFTS()
    varlist = []

    for i in ['Position', 'Velocity', 'Acceleration']:
        for j in ['Current', 'Setpoint']:
            for n in range(3):
                varlist.append('Group'+str(n)+'.Pos.'+j + i)

    fts.initialize('192.168.0.254','Administrator','xxxxxxxxx')
    
    print('Status: Finish initialization')
    fts.status()
    ##############################
    # test0
    stage = fts.newportxps.stages['Group1.Pos']
    print('***********************')
    pos = fts.newportxps.get_stage_position('Group1.Pos')
    print(pos)
    #fts.configure(50,0)
    times = []
    poss = []
    for i in range(7, 100):
        fts.configure(i,0)
        x = fts.newportxps.get_stage_position('Group2.Pos')
        time0 = time.time()
        times.append(time0)
        poss.append(x)
    plt.plot(times, poss)
    plt.show()
    '''
    cmd = "GroupMoveAbsolute(Group1.Pos, 30)  GroupMoveAbsolute(Group2.Pos, 60) GroupMoveAbsolute(Group1.Pos, 100) GroupMoveAbsolute(Group2.Pos, 0)  ; "
    x=fts.newportxps._xps.Send(cmd=cmd)
    print(x)
    print('***********************')
    
    print(fts.newportxps.get_stage_position('Group1.Pos'))
    print(fts.newportxps.get_stage_position('Group2.Pos'))
    print('Status: Set configure')
    ##################
    ## test 1
    

    print('here')
    #fts.scan(varlist)
    ##################
    ## test 2
    # fts.scan_event(varlist)
    ##################
    #    test 3
    fts.configure(100, 0)
    print('***********************')
    print(fts.newportxps.get_stage_position('Group1.Pos'))
    print(fts.newportxps.get_stage_position('Group2.Pos'))
    fts.configure(8,5)
    print('***********************')
    print(fts.newportxps.get_stage_position('Group1.Pos'))
    print(fts.newportxps.get_stage_position('Group2.Pos'))
    
    # ##############
    '''
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
if __name__ == '__main__':
    main()
