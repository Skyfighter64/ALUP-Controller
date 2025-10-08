import datetime
import time
import math
import multiprocessing
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

Test for the experimental buffering branch.
Tests latencies, time stamps, drift, etc.
for one or multiple grouped devices

"""

MEASUREMENTS = 30000
NUM_DEVICES = 1

TIME_DELTA_BUFFER_SIZE=100

group = Group()

# log to a file in the logs folder
#logging.basicConfig(filename="../logs/latest.log", filemode="w+", format="[%(asctime)s %(levelname)s %(funcName)s l.%(lineno)d]: %(message)s", datefmt="%H:%M:%S")
# log to the terminal directly
logging.basicConfig(format="[%(asctime)s %(levelname)s]: %(message)s", datefmt="%H:%M:%S")
#logging.getLogger(pyalup.__name__).setLevel(logging.INFO)
"""
NOTE: Some data represents true measurement results while other data is marked as estimate or corrected.
Estimated/Corrected data was corrected in its time domain by adding time_delta, therefore it is bound to 
the accuracy of the time synchronization and contains the time synchronization error.
"""

time_deltas = [[] for _ in range(NUM_DEVICES)]  # the time deltas of each device (smoothed)
time_deltas_raw = [[] for _ in range(NUM_DEVICES)]  # the raw time deltas of each device

sender_times = [[] for _ in range(NUM_DEVICES)] # the time at which the data was recorded on the sender  

receiver_time_estimates = [[] for _ in range(NUM_DEVICES)]   # calculated (estimated) receiver time
receiver_out_times = [[] for _ in range(NUM_DEVICES)]   # time when receiver sent out packets; this is representative for the receiver's internal time

tx_latencies = [[] for _ in range(NUM_DEVICES)]  # sending latency (corrected): Latency for sending a fame from the sender to the receiver
rx_latencies = [[] for _ in range(NUM_DEVICES)]  # receiving latency (corrected): Latency for sending an Acknowledgement from the receiver to the sender
latencies = [[] for _ in range(NUM_DEVICES)]  # the communication latency of a Send() call (From sending frame to receiving ANY Acknowledgement)
frame_rtts = [[] for _ in range(NUM_DEVICES)] # the round trip time of one frame (From sending frame to receiving ITS OWN Acknowledgement)

timestamp_errors = [[] for _ in range(NUM_DEVICES)] # the difference of the actual packet time stamp to the receiver's reported timestamp after applying the packet (corrected)

# Error of the Sender's time estimate for the receiver's local time: The difference of the receiver's reported packet outgoing time stamp vs the Sender's estimate of the receiver time at the point of receiving the Acknowledgement
# NOTE: the raw time estimate error does also include the rx latency, which is removed in the corrected time estimate error
time_estimate_errors = [[] for _ in range(NUM_DEVICES)] 
time_estimate_errors_corrected = [[] for _ in range(NUM_DEVICES)] # error of the estimate of the receiver time stamp with the corrected rx latency subtracted

receiver_packet_processing_times = [[] for _ in range(NUM_DEVICES)] # the time from the sender receiving a frame to the receiver sending out the acknowledgement
openResponses = [[] for _ in range(NUM_DEVICES)] # the number of unanswered frames on the Sender. Correlates directly to the buffer usage on the receiver
group_latencies = [] # worst-case device latency of any member of the group

runtime = 0

def main():
    global runtime

    print("ALUP timestamp accuracy test")
    # connect to the controller
    print("Connecting...")
    dut = Device(_time_delta_buffer_size=TIME_DELTA_BUFFER_SIZE)
    dut.SerialConnect("COM6", 115200)
    #dut.SerialConnect("COM8", 115200)
    #dut.TcpConnect("192.168.180.112", 5012)
    print("Connected")
    print(dut.configuration)
    
    """
    print("Connecting...")
    dut2 = Device(_time_delta_buffer_size=TIME_DELTA_BUFFER_SIZE)
    #dut2.SerialConnect("COM6", 115200)
    dut2.TcpConnect("192.168.180.112", 5012)
    print("Connected")
    print(dut2.configuration)
    
    
    print("Connecting...")
    dut3 = Device(_time_delta_buffer_size=TIME_DELTA_BUFFER_SIZE)
    #dut3.SerialConnect("COM4", 115200)
    dut3.TcpConnect("192.168.180.112", 5012)
    print("Connected")
    print(dut3.configuration)

    print("Connecting...")
    dut4 = Device(_time_delta_buffer_size=TIME_DELTA_BUFFER_SIZE)
    #dut3.SerialConnect("COM4", 115200)
    dut4.TcpConnect("192.168.180.111", 5012)
    print("Connected")
    print(dut4.configuration)
    """
    group.Add(dut)
    #group.Add(dut2)
    #group.Add(dut3)
    #group.Add(dut4)

    # send some frames to get a first calibration for the time offset
    
    print("Calibrating time delta")
    for i in tqdm(range(100)):
        group.SetColors([]) #TODO: with TCP this  takes very long (why?)
        group.Send()
    print("Flushing Buffers")
    for device in tqdm(group.devices):
        device.FlushBuffer()
    print("Done")

    # assign logging callbacks for each device
    for idx, device in enumerate(group.devices):
        print("Registered callback for device " + str(idx))
        device._onFrameResponse = functools.partial(log_device_stats, idx)
    
    start = time.time()

    #next_timestamp = time.time_ns() // 1000000

    try:
        for i in tqdm(range(MEASUREMENTS)):
            

            # schedule a frame every n ms
            #for i in range(NUM_DEVICES):
            #    group.devices[i].frame.timestamp = next_timestamp
            #next_timestamp += 50

            # turn on the led at exactly the next second
            group.SetColors([0xff0000] * 100)
            group.Send()

            # schedule a frame every n ms
            #for i in range(NUM_DEVICES):
            #    group.devices[i].frame.timestamp = next_timestamp
            #next_timestamp += 50

            # turn off the led at exactly the next second
            # NOTE: don't use clear command here to simulate a lot of data / even data flow
            #group.SetColors([0x000000] * dut.configuration.ledCount)
            #group.Send() 

    except KeyboardInterrupt:
        pass
    
    group.Disconnect()
    runtime = time.time() - start
    print("\n-------------[Done]-------------")
    print("Total runtime: " + str(time.strftime('%Hh:%Mm:%Ss', time.gmtime(runtime))))
    print("Measurements: " + str(len(sender_times[0])))
    print("Device Processing Time:")
    print_summary("Device Processing Time", receiver_packet_processing_times)
    print_drift()
    print("-----------------------------")
    plot_stats()



def print_time():
    print(chr(27) + "[2J") # clear screen
    print("Current time:")
    while True:
        print(datetime.datetime.now().strftime('%H:%M:%S:%f (H:M:S:us)'), end="\r", flush=True)


def print_drift():
    for i in range(NUM_DEVICES):
        print("\nDevice " + str(i) + " Drift:")
        try: 
            receiver_true_time_drift = GetDrift(sender_times[i], receiver_out_times[i])
            receiver_estimated_time_drift = GetDrift(sender_times[i], receiver_time_estimates[i])

            receiver_true_time_slope = GetSlope(sender_times[i], receiver_out_times[i])

            print(f"True time drift: { receiver_true_time_drift:.10f} s/s or {receiver_true_time_drift * (60*60*24)} s/day")
            print(f"Time drift correction factor: {1/receiver_true_time_slope}")
            print(f"Estimated time drift: {receiver_estimated_time_drift:.10f} s/s or {receiver_estimated_time_drift * (60*60*24)} s/day")
        except ZeroDivisionError:
            print("Could not calculate drift. Not enough data points")


def print_summary(variable_name, data):
    print(variable_name + " Summary:")
    for i in range(NUM_DEVICES):
        print(f"Device {str(i)}:")
        print_mean(data[i])


def print_mean(data):
    """
    Print a summary of a given list of numbers
    """
    print("\tMean: %fms, Variance: %fms\n\t(Min: %fms, Max: %fms, Range: %fms) " % (statistics.mean(data), statistics.variance(data), min(data), max(data), max(data) - min(data) ))


# @param i: the index of the device for which to log the stats
# @param frame: the frame from which the data is logged
def log_device_stats(i, frame):
    # save current times
    sender_time = (time.time_ns() // 1000000)
    sender_times[i].append(sender_time)
    device = group.devices[i]

    time_deltas[i].append(device.time_delta_ms)
    time_deltas_raw[i].append(device._time_delta_ms_raw)

    receiver_time_estimate = device.time_delta_ms + sender_time
    receiver_time_estimates[i].append(receiver_time_estimate)
    receiver_out_times[i].append(frame._t_receiver_out)


    # calculate rx and tx latencies (with correction)
    tx_latency = frame._t_receiver_in - (frame._t_frame_out + device.time_delta_ms)
    rx_latency = (frame._t_response_in + device.time_delta_ms) - frame._t_receiver_out
    tx_latencies[i].append(tx_latency)
    rx_latencies[i].append(rx_latency)
    frame_rtts[i].append(frame._t_response_in - frame._t_frame_out)

    # get difference of reported sender out-time to frames time stamp
    timestamp_error = frame._t_receiver_out - frame.timestamp - device.time_delta_ms
    timestamp_errors[i].append(timestamp_error)

    # get the error of the estimated time to the true time
    time_estimate_error = receiver_time_estimate - frame._t_receiver_out
    time_estimate_errors[i].append(time_estimate_error)
    time_estimate_error_corrected = time_estimate_error - rx_latency
    time_estimate_errors_corrected[i].append(time_estimate_error_corrected)

    receiver_packet_processing_times[i].append(frame._t_receiver_out - frame._t_receiver_in)
    openResponses[i].append(len(device._unansweredFrames))

    # save true RTT latency
    latencies[i].append(device.latency)




def GetDrift(data_x, data_y):
    return GetSlope(data_x, data_y) - 1

def GetSlope(data_x, data_y):
    median_size = 25

    # get the median and index of the first n values
    start_index, start_median = argmedian(data_y[:median_size])

    # get the median and index of the last n values    
    end_index, end_median = argmedian(data_y[-median_size:])
    
    return (end_median - start_median) / (data_x[-median_size:][end_index] - data_x[:median_size][start_index])


def argmedian(data):
    """
    return the median of the given data together with its index in data
    if data is of even size, the lower value will be returned
    @param data: a list of sortable elements
    
    @returns (index, median)
    """

    indices = np.argsort(data)
    return (indices[len(data) // 2], data[indices[len(data) // 2]])

def plot_stats():
     # Create plot
    fig = plt.figure(figsize=(16, 8))
    plt.rcParams['figure.constrained_layout.use'] = True
    gs = fig.add_gridspec(math.ceil(((len(latencies) + 7) / 2)) , 2, hspace=0, wspace=0)
    axes = gs.subplots().flat
    fig.suptitle('Buffering Test')

    colors = plt.rcParams["axes.prop_cycle"]()

    """
    text = f'Total runtime: {time.strftime("%Hh:%Mm:%Ss", time.gmtime(runtime))} ({str(len(sender_times[i]))} Measurements) + Time Delta Buffer: {TIME_DELTA_BUFFER_SIZE}'
    for i in range(NUM_DEVICES):
        receiver_true_time_drift = GetDrift(sender_times[i], receiver_out_times[i])
        receiver_estimated_time_drift = GetDrift(sender_times[i], receiver_time_estimates[i])
        text += f'\nDev. {str(i)} local time drift:        {receiver_true_time_drift:.10f} s/s or {receiver_true_time_drift*(60*60*24):.5f} s/day\
                 \nDev. {str(i)} corrected time drift: {receiver_estimated_time_drift:.10f} s/s or {receiver_estimated_time_drift*(60*60*24):.5f} s/day'
    
    axes[0].text(0.05, 0.9, text,
                 horizontalalignment='left',verticalalignment='top',transform = axes[0].transAxes)
    """

    for i in range(len(openResponses)):
        color = next(colors)["color"]
        axes[0].plot(sender_times[i], openResponses[i],color=color, label= "Dev. " + str(i) + " Open Responses (Max. " + str(group.devices[i].configuration.frameBufferSize) + ")")
    
    # reset color cycle
    colors = plt.rcParams["axes.prop_cycle"]()

    # plot everything relative to sender time 
    # plot time_delta
    for i in range(len(time_deltas)):
        color = next(colors)["color"]
        axes[1].plot(sender_times[i], time_deltas[i],color=color, label= "Dev. " + str(i) + " Time Delta (median)")
        axes[1].plot(sender_times[i], time_deltas_raw[i], color=color, alpha=0.5, label = "Dev. " + str(i) + " Time Delta (Raw)")
    
    # reset color cycle
    colors = plt.rcParams["axes.prop_cycle"]()

    # plot local times
    for i in range(len(frame_rtts)):
        color = next(colors)["color"]
        axes[2].plot(sender_times[i], [frame_rtts[i][j] - latencies[i][j] for j in range(len(frame_rtts[i]))] , color=color, label = "Dev. " + str(i) + "Frame RTT vs. Latency")
        #axes[2].plot(sender_times[i], receiver_out_times[i], color=color, alpha=0.5, label = "Dev. " + str(i) + " time (true)")

    colors = plt.rcParams["axes.prop_cycle"]()
    # plot time stamp error
    for i in range(len(timestamp_errors)):
        color = next(colors)["color"]
        axes[3].plot(sender_times[i], timestamp_errors[i], color=color, label = "Dev. " + str(i) + " time stamp error")

    colors = plt.rcParams["axes.prop_cycle"]()
    # plot time estimation errors
    for i in range(len(time_estimate_errors)):
        color = next(colors)["color"]
        axes[4].plot(sender_times[i], time_estimate_errors[i], color=color, alpha=0.3, label = "Dev. " + str(i) + " time est. error")
        axes[4].plot(sender_times[i], time_estimate_errors_corrected[i], color=color, alpha=0.8, label = "Dev. " + str(i) + " time est. error (corr.)")

    #axes[5].plot(sender_times[0], group_latencies, color=color, label = "Group Latency")

    for i in range(len(receiver_packet_processing_times)):
        color = next(colors)["color"]
        axes[6].plot(sender_times[i], receiver_packet_processing_times[i], color=color, label = "Dev. " + str(i) + " packet processing")

    for i in range(len(latencies)):
        axes [7 + i].plot(sender_times[i], rx_latencies[i], color=next(colors)["color"], alpha = 0.5, label = "Dev. " + str(i) + " RX Latency (est.)")
        axes [7 + i].plot(sender_times[i], tx_latencies[i], color=next(colors)["color"], alpha = 0.5, label = "Dev. " + str(i) + " TX Latency (est.)")
        axes [7 + i].plot(sender_times[i], latencies[i], color=next(colors)["color"], alpha = 0.9, label = "Dev. " + str(i) + " Latency")
        axes [7 + i].plot(sender_times[i], frame_rtts[i], color=next(colors)["color"], alpha = 0.9, label = "Dev. " + str(i) + " Frame RTT")
    
    # make all ticks of uneven plot numbers to the right side
    for ax in fig.get_axes()[1::2]:
        ax.yaxis.tick_right()

    # configure all axes to look good
    for ax in fig.get_axes():
        #ax.label_outer()
        ax.sharex(axes[1])
        #ax.set_xlabel('Packet')
        ax.set_xlabel('system time (ms)')
        ax.set_ylabel('ms')
        ax.grid()
        ax.legend()

    for ax in fig.get_axes()[4:]:
        ax.set_ylim(bottom=-20) 
    fig.tight_layout()
    # Show plot
    plt.show()


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