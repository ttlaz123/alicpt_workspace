
#from newportxps import NewportXPS
from newportxps.newportxps.newportxps import NewportXPS

xps = NewportXPS('192.168.0.254', username='Administrator', password='Administrator')
xps.initialize_allgroups()
xps.home_allgroups()

print()
print('Check Status: Status should be Ready')
print(xps.status_report())

# Group1: IMS500CCHA
# Group2: IMS500CC
# Group3: PR50CC

print()
print('Status: Set Max Velocity')  ## unit: mm/s
xps.set_velocity('Group1.Pos',20)  
xps.set_velocity('Group2.Pos',20)  
xps.set_velocity('Group3.Pos',10)  

print('Status: Set the Initial position')
xps.move_stage('Group1.Pos',250)
xps.move_stage('Group2.Pos',250)
xps.move_stage('Group3.Pos',0)

print('Status: Slowly Move the Stage')
xps.move_stage('Group1.Pos',150,1)
xps.move_stage('Group2.Pos',-150,1)
xps.move_stage('Group3.Pos',90,1)

print('Status: Print Current Position')
print('Stage1: {:.2f}'.format(xps.get_stage_position('Group1.Pos')))
print('Stage2: {:.2f}'.format(xps.get_stage_position('Group2.Pos')))
print('Stage3: {:.2f}'.format(xps.get_stage_position('Group3.Pos')))

print()
print('Test Finish!')
