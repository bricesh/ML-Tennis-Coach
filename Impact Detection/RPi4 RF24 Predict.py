import time
from RF24 import *
import struct
import signal as sig
import csv
import random as rd
import sys

from joblib import load
from scipy import signal
import pandas as pd
import numpy as np

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
mean_x = 0.0
mean_y = 0.0
mean_z = 0.0
init = 1
clfGB = load('/home/pi/Documents/MPU/impact_classifier_GB.skm')

def get_prediction(samples):
    acc_data = pd.DataFrame(samples, columns=['x','y','z'])
    features = pd.DataFrame([[calc_slopes(acc_data), calc_lag(acc_data), calc_peak_freq(acc_data)]], columns=['slopes', 'xy_lag', 'peak_freqs'])
    features = pd.concat([features.drop(['slopes'], axis=1), features['slopes'].apply(pd.Series)], axis=1)
    features = pd.concat([features.drop(['peak_freqs'], axis=1), features['peak_freqs'].apply(pd.Series)], axis=1)
    return clfGB.predict(features[['xy_lag', 'peak_freq1', 'slope1', 'slope2']])
    
def calc_lag(impact_data):
    x_data = impact_data['x']
    y_data = impact_data['y']
    corr = np.correlate(x_data - mean_x, y_data - mean_y, mode='full')
    lag = corr.argmax() - (len(x_data) - 1)
    return lag

def calc_slopes(impact_data):
    z_data = impact_data['z']
    slope1 = np.mean(abs(z_data[0:50] - mean_z)) - np.mean(abs(z_data[50:100] - mean_z))
    slope2 = np.mean(abs(z_data[100:150] - mean_z)) - np.mean(abs(z_data[150:200] - mean_z))
    return {'slope1': slope1, 'slope2': slope2}

def calc_peak_freq(impact_data):
    sampling_freq = 500
    impact_data_z = impact_data['z'] - mean_z
    window = signal.windows.hann(len(impact_data_z)) #force-exp is apparently the best option...
    fourierTransform = np.fft.fft(window * (impact_data_z)) / len(impact_data_z)
    fourierTransform = fourierTransform[range(int(len(impact_data_z) / 2))]
    tpCount = len(impact_data_z)
    values = np.arange(int(tpCount/2))
    timePeriod = tpCount/sampling_freq
    frequencies = values/timePeriod
    peak_freq1 = frequencies[np.argmax(abs(fourierTransform))]
    fourierTransform[np.argmax(abs(fourierTransform))] = 0
    peak_freq2 = frequencies[np.argmax(abs(fourierTransform))]
    peak_freq = [peak_freq1, peak_freq2]
    return {'peak_freq1': max(peak_freq), 'peak_freq2': min(peak_freq)}

def signal_handler(sig, frame):
    sys.exit(0)

def try_read_data(channel=0):
    if radio.available():
        while radio.available():
            len = radio.getDynamicPayloadSize()
            receive_payload = radio.read(len)
            if len == 6:
                [x,y,z] = struct.unpack('3h', receive_payload)
                samples.append([x, y, z])
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
sig.signal(sig.SIGINT, signal_handler)

# forever loop
while 1:
    try_read_data()
    if (not (len(samples) == 0) and len(samples) % 200 == 0):
        print(len(samples))
        if init == 1:
            [mean_x, mean_y, mean_z] = [sum(xyz_vals)/len(xyz_vals) for xyz_vals in list(map(list, zip(*samples)))]
            print([mean_x, mean_y, mean_z])
            init = 0
        else:
            impact_loc = get_prediction(samples)
            print('\nImpact location: ', impact_loc)
        samples = []
