import datetime
import time
import math
import multiprocessing
import logging
from tqdm import tqdm

from pyalup.Device import Device

process = None

def main():
    #logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    print("ALUP timestamp accuracy test")
    # connect to the controller
    print("Connecting...")
    dut = Device()
    dut.SerialConnect("COM6", 115200)
    #dut.TcpConnect("192.168.180.111", 5012)
    print("Connected")
    print(dut.configuration)
    
    # send some frames to get a first calibration for the time offset
    print("Calibrating time delta")
    for i in tqdm(range(100)):
        dut.SetColors([0x000000])
        dut.frame.timestamp = 0
        dut.Send()
    print("Done")


    print("Starting Clock")
    process = multiprocessing.Process(target=print_time)
    process.start()

    while True:
        # turn on the led at exactly the next second
        dut.frame.colors = [0xff0000]
        dut.frame.timestamp = ((time.time_ns() // 1000000000) + 1) * 1000 # add one second to the current time and convert it to ms
        print("now: " + str(time.time()) + " timestamp: " + str(dut.frame.timestamp))
        print("Receiver current local time: " + str((time.time_ns() // 1000000) + dut.time_delta_ms))
        dut.Send()

        # turn off the led at exactly the next second
        dut.frame.colors = [0x000000]
        dut.frame.timestamp = ((time.time_ns() // 1000000000) + 1) * 1000 # add one second to the current time and convert it to ms
        dut.Send()

    dut.Disconnect()

def print_time():
    print(chr(27) + "[2J") # clear screen
    print("Current time:")
    while True:
        print(datetime.datetime.now().strftime('%H:%M:%S:%f (H:M:S:us)'), end="\r", flush=True)



    

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        process.terminate()
        print(e)