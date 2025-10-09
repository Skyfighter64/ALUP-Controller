import datetime
import time
import math
import logging
import colorsys
import functools
from tqdm import tqdm
import statistics
import numpy as np

import pyalup
from pyalup.Device import Device
from pyalup.Group import Group

from matplotlib import pyplot as plt


"""
A simple long time test, with minimal logging, monitoring, etc..
"""

MAX_MEASUREMENTS = 10_000_000
TIME_DELTA_BUFFER_SIZE=100


# log to a file in the logs folder
#logging.basicConfig(filename="../logs/latest.log", filemode="w+", format="[%(asctime)s %(levelname)s %(funcName)s l.%(lineno)d]: %(message)s", datefmt="%H:%M:%S")
# log to the terminal directly
logging.basicConfig(format="[%(asctime)s %(levelname)s]: %(message)s", datefmt="%H:%M:%S")
#logging.getLogger(pyalup.__name__).setLevel(logging.DEBUG)

runtime = 0

def main():
    global runtime
    # count the number of measurements
    measurements = 0

    print("ALUP longtime endurance test")
    # connect to the controller
    print("Connecting...")
    dut = Device(_time_delta_buffer_size=TIME_DELTA_BUFFER_SIZE)
    #dut.SerialConnect("COM6", 115200)
    #dut.SerialConnect("COM8", 115200)
    dut.TcpConnect("192.168.180.112", 5012)
    print("Connected")
    print(dut.configuration)

    # send some frames to get a first calibration for the time offset
    
    print("Calibrating time delta")
    for i in tqdm(range(100)):
        #group.SetColors([0x000000])
        dut.SetColors([])
        dut.Send()

    print("Flushing Buffers")
    dut.FlushBuffer()

    print("Done")
    
    start = time.time()
    next_timestamp = time.time_ns() // 1000000
    try:
        for i in tqdm(range(MAX_MEASUREMENTS)):
            # turn on the led exactly every n ms
            dut.frame.timestamp = next_timestamp
            next_timestamp += 100
            dut.SetColors([0xff0000] * 100)
            dut.Send()
            measurements += 1

            #dut.frame.timestamp = next_timestamp
            #next_timestamp += 30
            # turn off the leds
            # NOTE: don't use clear command here to simulate a lot of data / even data flow
            #dut.SetColors([0x000000] * dut.configuration.ledCount)
            #dut.Send() 
            #measurements += 1

    except KeyboardInterrupt:
        pass
    
    #dut.Clear()
    dut.Disconnect()
    runtime = time.time() - start
    print("\n-------------[Done]-------------")
    print("Total runtime: " + str(time.strftime('%Hh:%Mm:%Ss', time.gmtime(runtime))))
    print(f"Total Measurements: {measurements} / {MAX_MEASUREMENTS}")
    print("-----------------------------")



def Rainbow(n, offset = 0, scale = 1.0):
    """Generate a rainbow effect

    Parameters:
    n: size of the returned RGB array
    offset: the offset of the HSV rainbow colors in positive index direction (Hue offset for each index).
    scale: the scaling factor for the rainbow color. scale < 1.0 stretches all colors while scale > 1.0 compresses them

    Returns:
    return_type: An array containing a rainbow effect for n LEDs
    """
    colors = []
    for i in range(n):
        colors.append(_RainbowColor(((i + offset)/n) * scale))
    return colors


def _RainbowColor(i):
    """generate a single rainbow color
    
    @param i: the hue for the generated color, in range [0.0, 1.0]
    @return: the 24bit hsv color
    
    """
    # make sure i is within 0, 1
    # this is needed because hsv_to_rgb behaves funky on negative values
    # sometimes giving back negative rgb values
    i = i % 1.0
    # get hsv color as rgb array
    color_array = colorsys.hsv_to_rgb(i, 1.0, 1.0)
    # scale array to range [0,255] and combine to hex color
    color = int(color_array[0] * 255)
    color = color << 8
    color += int(color_array[1] * 255)
    color = color << 8
    color += int(color_array[2] * 255)
    return color
    

if __name__ == "__main__":
    main()