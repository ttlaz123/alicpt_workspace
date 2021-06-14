# python3
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Glazier interface to NTP time service."""


import time
import ntplib


def get_network_time():
    NTPserver = ['pool.ntp.org','time.stanford.edu']
    c = ntplib.NTPClient()
    ntpResponse = 0
    for server in NTPserver:
        try:
            ntpResponse = c.request(server)
            #print('NTP SERVER: ' + server)
            break
        except:
            pass


    if (ntpResponse): return ntpResponse.tx_time
    else: return None

def get_time_diff():

    ntpResponse = get_network_time()
    if (ntpResponse):
        diff = time.time() - ntpResponse
        return diff

    else: return None

print(time.ctime(get_network_time()))
print(get_time_diff())

print('#######################################################')
dt = get_time_diff()
print(dt)
t1 = get_network_time() - dt
print('START TIME:\t'+str(t1)+' |\t'+time.ctime(t1))
time.sleep(1)
t2 = get_network_time() - dt
print('END TIME:\t'+str(t2)+' |\t'+time.ctime(t2))

fp = open("timestamp.dat", "a")

fp.write('#######################################################\n')
fp.write(str(dt)+'\n')
fp.write('START TIME:\t'+str(t1)+' |\t'+time.ctime(t1)+'\n')
fp.write('END TIME:\t'+str(t2)+' |\t'+time.ctime(t2)+'\n')

fp.close()