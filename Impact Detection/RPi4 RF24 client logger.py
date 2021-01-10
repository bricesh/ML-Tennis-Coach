import time
from RF24 import *
import struct
import signal
import csv
import random as rd
import sys

########### USER CONFIGURATION ###########
# See https://github.com/TMRh20/RF24/blob/master/pyRF24/readme.md
# CE Pin, CSN Pin, SPI Speed
# Setup for GPIO 22 CE and CE0 CSN with SPI Speed @ 8Mhz
radio = RF24(22, 0)

samples = []
prev_samples_len = 0
impact_no = 0
impact_locations = ['TL', 'BL', 'MC', 'TR', 'BR']
impact_loc = ''

def signal_handler(sig, frame):
    with open('acc_data_new.csv', mode='w') as sensor_readings:
        sensor_write = csv.writer(sensor_readings,
                                  delimiter=',',
                                  quotechar='"',
                                  quoting=csv.QUOTE_MINIMAL)
        sensor_write.writerow(['x','y','z','pos'])
        sensor_write.writerows(samples)
    sys.exit(0)

def try_read_data(channel=0):
    if radio.available():
        while radio.available():
            len = radio.getDynamicPayloadSize()
            receive_payload = radio.read(len)
            if len == 6:
                [x,y,z] = struct.unpack('3h', receive_payload)
                samples.append([x, y, z, impact_loc])
            else:
                mode = struct.unpack('?', receive_payload)
                print(mode)

pipes = [0xF0F0F0F0E1]#, 0xF0F0F0F0D2]
radio.begin()
radio.setDataRate(RF24_2MBPS)
radio.setPALevel(RF24_PA_MIN)
radio.setAutoAck(False);
radio.enableDynamicPayloads()
radio.setRetries(5,15)
radio.printDetails()
radio.openReadingPipe(1,pipes[0])
radio.startListening()

#Keyboard Ctrl-C detector
signal.signal(signal.SIGINT, signal_handler)

# forever loop
while 1:
    try_read_data()
    if (not (prev_samples_len == len(samples)) and len(samples) % 200 == 0):
        prev_samples_len = len(samples)
        print(len(samples))
        impact_loc = rd.choice(impact_locations)
        print('\nNext target: ', impact_loc)
