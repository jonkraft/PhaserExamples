#!/usr/bin/env python3
#  Must use Python 3
# Copyright (C) 2022 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

''' Simple Beamforming Example Using Phaser and Python'''

# =============================================================================
# Import statements
# =============================================================================
import adi
import ADAR_pyadi_functions as ADAR  # import the ADAR1000 functions
import SDR_functions as SDR  # import the Pluto SDR functions

import sys
import pickle
import matplotlib.pyplot as plt
import numpy as np



# =============================================================================
# User parameters
# =============================================================================

rpi_ip = "ip:phaser.local"  # default IP address of Phaser's Raspberry Pi
sdr_ip = "ip:192.168.2.1"   # default Pluto IP address

# select which signal source to use
# HB100 (external source)
# OUT1  (transmit freq is set in config.py)
# OUT2  (transmit freq is set in config.py)
SignalSource = 'HB100'     # 'HB100', 'OUT1', or 'OUT2'

# config.py has all the key parameters that you might want to modify
try:
    import config as config
except:
    print("Make sure config.py is in this directory")
    sys.exit(0)


# =============================================================================
# Variables setup
# =============================================================================

# if using HB100, load the signal frequency from "phaser_find_hb100.py" output file
if SignalSource == 'HB100':
    try:
        with open("hb100_freq_val.pkl", "rb") as file1: 
            config.SignalFreq = pickle.load(file1)
        print("Found signal freq file, ", config.SignalFreq/1e9, " GHz")
    except:
        print("No signal freq found, keeping at ", config.SignalFreq/1e9, " GHz")

"""SET DEFAULT VALUES"""
sdr_address = sdr_ip
SignalFreq = config.SignalFreq
Tx_freq = config.Tx_freq  # Pluto's Tx LO freq.
Rx_freq = config.Rx_freq  # Pluto's Rx LO freq
LO_freq = SignalFreq + Rx_freq  # freq of the LTC5548 mixer LO
SampleRate = config.SampleRate
Rx_gain = config.Rx_gain
Tx_gain = config.Tx_gain
RxGain1 = 100
RxGain2 = 100
RxGain3 = 100
RxGain4 = 100
RxGain5 = 100
RxGain6 = 100
RxGain7 = 100
RxGain8 = 100
RxPhase1 = config.Rx1_cal
RxPhase2 = config.Rx2_cal
RxPhase3 = config.Rx3_cal
RxPhase4 = config.Rx4_cal
RxPhase5 = config.Rx5_cal
RxPhase6 = config.Rx6_cal
RxPhase7 = config.Rx7_cal
RxPhase8 = config.Rx8_cal
phase_step_size = 2.8125
c = 299792458  # speed of light in m/s
d = config.d   # antenna spacing for phaser is 14mm
gainList = [RxGain1, RxGain2, RxGain3, RxGain4,
    RxGain5, RxGain6, RxGain7, RxGain8]
phaseList = [RxPhase1, RxPhase2, RxPhase3, RxPhase4,
    RxPhase5, RxPhase6, RxPhase7, RxPhase8]


# =============================================================================
# Hardware setup
# =============================================================================

# Use the onboard VCO to generate the LO?  Or apply source to EXT_LO?
gpios = adi.one_bit_adc_dac(rpi_ip)
gpios.gpio_vctrl_1 = 1  # 1=Use onboard PLL/LO source  (0=use external LO input)
gpios.gpio_vctrl_2 = 1  # 1=Send LO to transmit circuitry  (0=disable Tx path and send LO to LO_OUT)

# setup GPIOs to control if Tx is output on OUT1 or OUT2
gpios.gpio_div_mr = 1
gpios.gpio_div_s0 = 0
gpios.gpio_div_s1 = 0
gpios.gpio_div_s2 = 0
  
# Initialize Pluto
sdr = SDR.SDR_init(
    sdr_address,
    SampleRate,
    Tx_freq,
    Rx_freq,
    Rx_gain,
    Tx_gain,
    config.buffer_size,
    )
SDR.SDR_LO_init(rpi_ip, LO_freq)  # Set Phaser's ADF4159 to the LO_freq

# Intialize the ADAR1000 receive array
rx_array = adi.adar1000_array(
    uri=rpi_ip,
    chip_ids=["BEAM0", "BEAM1"],  # these are the ADAR1000s' labels in the device tree
    device_map=[[1], [2]],
    element_map=[[1, 2, 3, 4, 5, 6, 7, 8]],
    device_element_map={
        1: [7, 8, 5, 6],  # i.e. channel2 of device1 (BEAM0), maps to element 8
        2: [3, 4, 1, 2],
        },
    )
for device in rx_array.devices.values():
    ADAR.ADAR_init(device)  # resets the ADAR1000
    ADAR.ADAR_set_mode(device, "rx")  # ADAR1000s on Phaser are receive only, so mode is always "rx"
ADAR.ADAR_set_Taper(
    rx_array,
    gainList
    )

# Set transmitter to either OUT1 or OUT2 SMA port.  Or disable if using HB100
if SignalSource == 'OUT1':    # use Phaser's OUT1 SMA port as the transmitter
    gpios.gpio_tx_sw = 1      # 0=OUT2, 1=OUT1
    gpios.gpio_vctrl_2 = 1    # 1=Send LO to transmit circuitry
elif SignalSource == 'OUT2':  # use OUT2 as the transmitter
    gpios.gpio_tx_sw = 0      # 0=OUT2, 1=OUT1
    gpios.gpio_vctrl_2 = 1    # 1=Send LO to transmit circuitry
else:   # use HB100 as the transmit signal source
    gpios.gpio_tx_sw = 0 
    SDR.SDR_setTx(sdr, -80) # disable tx output by attenuating it


# =============================================================================
# Define Common Functions
# =============================================================================
def ConvertPhaseToSteerAngle(PhDelta):
        # steering angle theta = arcsin(c*deltaphase/(2*pi*f*d)
    value1 = (c * np.radians(np.abs(PhDelta))) / (
        2 * 3.14159 * (SignalFreq) * d)
    clamped_value1 = max(min(1, value1), -1)  # arcsin argument must be between 1 and -1
    theta = np.degrees(np.arcsin(clamped_value1))
    if PhDelta >= 0:
        SteerAngle = theta  # positive PhaseDelta covers 0deg to 90 deg
    else:
        SteerAngle = -theta  # negative phase delta covers 0 deg to -90 deg
    return SteerAngle

def dbfs(raw_data):
    # function to convert IQ samples to FFT plot, scaled in dBFS
    NumSamples = len(raw_data)
    win = np.hamming(NumSamples)
    y = raw_data * win
    s_fft = np.fft.fft(y) / np.sum(win)
    s_shift = np.fft.fftshift(s_fft)
    s_dbfs = 20*np.log10(np.abs(s_shift)/(2**11))     # Pluto is a signed 12 bit ADC, so use 2^11 to convert to dBFS
    return s_dbfs


# =============================================================================================
# Loop through all the steering angles and record the peak FFT amplitude at each steering angle
# =============================================================================================
angles = []       # stores the list of steering angles
peak_gains = []   # stores the peak FFT gain received for each steering angle

steering_step = 1  # steering angle step size (in degrees)
SteerValues = np.arange(-90, 90 + steering_step, steering_step)
# Phase delta = 2*Pi*d*sin(theta)/lambda = 2*Pi*d*sin(theta)*f/c
PhaseValues = np.degrees(
    2*np.pi*d* np.sin(np.radians(SteerValues))
    * SignalFreq / c
)

for PhDelta in PhaseValues:
    ADAR.ADAR_set_Phase(
        rx_array,
        PhDelta,
        phase_step_size,
        phaseList
    )
    
    data = sdr.rx()
    data_sum = data[0]+data[1]
    sum_dbfs = dbfs(data_sum)
    peak_dbfs = max(sum_dbfs)
    angles.append(ConvertPhaseToSteerAngle(PhDelta))
    peak_gains.append(peak_dbfs)
    
    
# =============================================================================
# Plotting results
# =============================================================================

plt.figure(1)
plt.subplot(2, 1, 1)
plt.title("Beam sweep plot")
plt.plot(angles, peak_gains, marker="o", ms=2)
plt.xlabel("Steering angle (deg)")
plt.ylabel("Peak Amplitude (dBFS)")
plt.tight_layout()
plt.show()

    
    
