#from newportxps import NewportXPS
from newportxps.newportxps.newportxps import NewportXPS
#from newportxps.newportxps import withConnectedXPS
from newportxps.newportxps.newportxps import withConnectedXPS
import posixpath

@withConnectedXPS
def downloadData(newportxps, filename='Gathering.dat'):
    """download text of data file
    Arguments:
    ----------
       newportxps (obj):  NewportXPS object
       filename  (str):   data file name
    """
    newportxps.ftpconn.connect(**newportxps.ftpargs)
    newportxps.ftpconn.cwd(posixpath.join(newportxps.ftphome, 'Public'))
    newportxps.ftpconn.save(filename, filename)
    newportxps.ftpconn.close()

xps = NewportXPS('192.168.0.254', username='Administrator', password='Administrator')
xps.initialize_allgroups()
xps.home_allgroups()

print()
print('Check Status: Status should be Ready')
print(xps.status_report())

# Group1: IMS500CCHA
# Group2: IMS500CC
# Group3: PR50CC
print('Print Hardware Status')
print(xps.get_hardware_status())

print()
groupname = 'Group1'
pos = 'Pos'
dataCol = xps._xps.GatheringListGet(xps._sid)
print(dataCol)
print('generate motion parameters')
varlist = []
for i in ['Position','Velocity','Acceleration']:
    for j in ['Current','Setpoint']:
        varlist.append(j+i)

print('Data record variables:')
print(varlist)
dataCol = []
for i in range(3):
    for j in varlist:
        dataCol.append('Group'+str(i+1)+'.Pos.'+j)

xps._xps.GatheringConfigurationSet(xps._sid,dataCol)
xps.move_stage('Group1.Pos',250)

print('Status: Finish config setting')
xps._xps.GatheringRun(xps._sid,100,8)
xps.move_stage('Group1.Pos',150,True)

#print('Status: Stop gathering')
#xps._xps.GatheringStop(xps._sid)
print('Status: Saving')
xps._xps.GatheringStopAndSave(xps._sid)
print('Status: Try to Download Data')
downloadData(xps,'Gathering.dat')

print()
print('Test Finish!')
