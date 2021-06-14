import logging
import math
import time

from newportxps import NewportXPS
# from newportxps.XPS_C8_drivers import XPSException
from pynput.keyboard import Listener, Key

# Setup logging
logging.basicConfig(filename="key_log.txt", level=logging.DEBUG, format='%(asctime)s %(message)s')

xps = NewportXPS('192.168.0.254', username='Administrator', password='Administrator')
xps.initialize_allgroups()
xps.home_allgroups()

# Group1: IMS500CCHA
# Group2: IMS500CC
# Group3: PR50CC

# INITIAL CONDITIONS
length1 = 0  # For Group1, mm
length = 250  # mm
angle = 45.0  # degrees
height = 700  # mm
angle_dependent = True
fast = False


def center_detector(number):  # Finds angle for a given position to hit center detector
    ideal_angle = math.degrees(math.atan(height / (math.sqrt((number - 250) ** 2 + height ** 2) + number - 250)))
    return ideal_angle


def upper_bound():  # upper boundary for stage 2
    boundary = 250 + height / math.tan(math.radians(72))  # 72 since 90 - 18
    return math.trunc(boundary)


def lower_bound():  # lower boundary for stage 2
    boundary = 250 + height / math.tan(math.radians(108))  # 108 since 90 + 18
    return math.trunc(boundary)


def move_stage1():
    for i in range(15):
        xps.move_stage('Group1.Pos', 150)
        xps.move_stage('Group1.Pos', 0)


print()
print('Check Status: Status should be Ready')
print(xps.status_report())

print()
print('Status: Set Max Velocity')  # unit: mm/s
xps.set_velocity('Group1.Pos', 5)
xps.set_velocity('Group2.Pos', 5)
xps.set_velocity('Group3.Pos', 5)

print('Status: Set the Initial position')
xps.move_stage('Group1.Pos', length1)  # Done near top of code
xps.move_stage('Group2.Pos', length)
xps.move_stage('Group3.Pos', angle)

print('Use Arrow Keys to move')
print('Esc button exits program!')
print('Space button changes angle dependence. Default True')
print('Enter button changes fast. Default False')
print('Left control button starts Stage1 motion')


def on_press(key):  # The function that's called when a key is pressed
    global length, angle, angle_dependent, fast
    if key == Key.enter:
        move_stage1()
    if key == Key.space:  # Space button changes angle dependency
        angle_dependent = not angle_dependent
        if angle_dependent:
            angle = center_detector(length)
            xps.move_stage('Group3.Pos', round(angle, 2))
            print('Fast: {}.  Angle Dependent: {}. Stage1: {:.2f} mm  Stage2: {:.2f} mm  Stage3: {:.2f}°'.format(fast,
                                                                                                                 angle_dependent,
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group1.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group2.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group3.Pos')))
            logging.info('Stage1: {:.2f} Stage2: {:.2f} Stage3: {:.2f}'.format(xps.get_stage_position(
                'Group1.Pos'), xps.get_stage_position('Group2.Pos'), xps.get_stage_position('Group3.Pos')))
        else:
            print('Fast: {}.  Angle Dependent: {}. Stage1: {:.2f} mm  Stage2: {:.2f} mm  Stage3: {:.2f}°'.format(fast,
                                                                                                                 angle_dependent,
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group1.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group2.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group3.Pos')))
    if key == Key.enter:
        fast = not fast  # enter key changes how fast this goes
        print('Fast: {}.  Angle Dependent: {}. Stage1: {:.2f} mm  Stage2: {:.2f} mm  Stage3: {:.2f}°'.format(fast,
                                                                                                             angle_dependent,
                                                                                                             xps.get_stage_position(
                                                                                                                 'Group1.Pos'),
                                                                                                             xps.get_stage_position(
                                                                                                                 'Group2.Pos'),
                                                                                                             xps.get_stage_position(
                                                                                                                 'Group3.Pos')))
    length_spacing = 1
    angle_spacing = .1
    if fast:
        length_spacing = 10
        angle_spacing = 1
    if lower_bound() <= length <= upper_bound():
        if key == Key.right:
            if length != upper_bound():
                length += length_spacing
            if angle_dependent:
                angle = center_detector(length)
            xps.move_stage('Group2.Pos', length)
            xps.move_stage('Group3.Pos', round(angle, 2))
            print('Fast: {}.  Angle Dependent: {}. Stage1: {:.2f} mm  Stage2: {:.2f} mm  Stage3: {:.2f}°'.format(fast,
                                                                                                                 angle_dependent,
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group1.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group2.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group3.Pos')))
            logging.info('Stage1: {:.2f} Stage2: {:.2f} Stage3: {:.2f}'.format(xps.get_stage_position(
                'Group1.Pos'), xps.get_stage_position('Group2.Pos'), xps.get_stage_position('Group3.Pos')))
        if key == Key.left:
            if length != lower_bound():
                length -= length_spacing
            if angle_dependent:
                angle = center_detector(length)
            xps.move_stage('Group2.Pos', length)
            xps.move_stage('Group3.Pos', round(angle, 2))
            print('Fast: {}.  Angle Dependent: {}. Stage1: {:.2f} mm  Stage2: {:.2f} mm  Stage3: {:.2f}°'.format(fast,
                                                                                                                 angle_dependent,
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group1.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group2.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group3.Pos')))
            logging.info('Stage1: {:.2f} Stage2: {:.2f} Stage3: {:.2f}'.format(xps.get_stage_position(
                'Group1.Pos'), xps.get_stage_position('Group2.Pos'), xps.get_stage_position('Group3.Pos')))
        if key == Key.up and not angle_dependent:
            angle += angle_spacing
            xps.move_stage('Group2.Pos', length)
            xps.move_stage('Group3.Pos', round(angle, 2))
            print('Fast: {}.  Angle Dependent: {}. Stage1: {:.2f} mm  Stage2: {:.2f} mm  Stage3: {:.2f}°'.format(fast,
                                                                                                                 angle_dependent,
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group1.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group2.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group3.Pos')))
            logging.info('Stage1: {:.2f} Stage2: {:.2f} Stage3: {:.2f}'.format(xps.get_stage_position(
                'Group1.Pos'), xps.get_stage_position('Group2.Pos'), xps.get_stage_position('Group3.Pos')))
        if key == Key.down and not angle_dependent:
            angle -= angle_spacing
            xps.move_stage('Group2.Pos', length)
            xps.move_stage('Group3.Pos', round(angle, 2))
            print('Fast: {}.  Angle Dependent: {}. Stage1: {:.2f} mm  Stage2: {:.2f} mm  Stage3: {:.2f}°'.format(fast,
                                                                                                                 angle_dependent,
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group1.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group2.Pos'),
                                                                                                                 xps.get_stage_position(
                                                                                                                     'Group3.Pos')))
            logging.info('Stage1: {:.2f} Stage2: {:.2f} Stage3: {:.2f}'.format(xps.get_stage_position(
                'Group1.Pos'), xps.get_stage_position('Group2.Pos'), xps.get_stage_position('Group3.Pos')))
    else:
        length = upper_bound() if length > 10 else lower_bound()
    if key == Key.esc:  # Esc button exits
        print('Motion Completed!')
        print('Status: Print Current Position')
        print('Stage1: {:.2f}'.format(xps.get_stage_position('Group1.Pos')))
        print('Stage2: {:.2f}'.format(xps.get_stage_position('Group2.Pos')))
        print('Stage3: {:.2f}'.format(xps.get_stage_position('Group3.Pos')))
        print('Test Finish!')
        time.sleep(10)
        exit(0)


with Listener(on_press=on_press) as listener:  # Create an instance of Listener
    listener.join()  # Join the listener thread to the main thread to keep waiting for keys
