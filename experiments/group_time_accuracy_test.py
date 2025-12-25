import datetime
import time
import math
import multiprocessing
import logging
import colorsys
from tqdm import tqdm
import statistics
import numpy as np

from pyalup.Device import Device
from pyalup.Group import Group

from matplotlib import pyplot as plt

"""

Test the accuracy of the time stamps for a group of devices

"""

MEASUREMENTS = 10000
NUM_DEVICES = 4

TIME_DELTA_BUFFER_SIZE=100

process = None

group = Group()


time_deltas = [[] for _ in range(NUM_DEVICES)]  
time_deltas_raw = [[] for _ in range(NUM_DEVICES)]  
sender_times = []   
receiver_time_estimates = [[] for _ in range(NUM_DEVICES)]   # calculated (estimated) receiver time
receiver_out_times = [[] for _ in range(NUM_DEVICES)]   # time when receiver sent out packets; this is representative for the receiver's internal time

tx_latencies = [[] for _ in range(NUM_DEVICES)]  
rx_latencies = [[] for _ in range(NUM_DEVICES)]  
latencies = [[] for _ in range(NUM_DEVICES)]  

timestamp_errors = [[] for _ in range(NUM_DEVICES)]
# NOTE: the time estimate error does also include the rx latency
time_estimate_errors = [[] for _ in range(NUM_DEVICES)]    
time_estimate_errors_corrected = [[] for _ in range(NUM_DEVICES)]    

receiver_packet_processing_times = [[] for _ in range(NUM_DEVICES)]    

group_latencies = []

runtime = 0

def main():
    global runtime
    #logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    print("ALUP timestamp accuracy test")
    # connect to the controller
    print("Connecting...")
    dut = Device(_time_delta_buffer_size=TIME_DELTA_BUFFER_SIZE)
    dut.SerialConnect("COM6", 115200)
    #dut.TcpConnect("192.168.180.111", 5012)
    print("Connected")
    print(dut.configuration)

    print("Connecting...")
    dut2 = Device(_time_delta_buffer_size=TIME_DELTA_BUFFER_SIZE)
    dut2.SerialConnect("COM4", 115200)
    #dut2.TcpConnect("192.168.180.111", 5012)
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

    group.Add(dut)
    group.Add(dut2)
    group.Add(dut3)
    group.Add(dut4)
    

    # send some frames to get a first calibration for the time offset
    print("Calibrating time delta")
    for i in tqdm(range(100)):
        group.SetColors([0x000000])
        group.Send()
    print("Done")

    #print("Synchronize timestamp")
    #time_stamp = (time.time_ns() // 1000000) + 1000
    #while (time.time_ns() // 1000000) < time_stamp:
    #    pass
    start = time.time()

    try:
        for i in tqdm(range(MEASUREMENTS)):
            # turn on the led at exactly the next second
            #group.SetColors([0xff0000])
            group.SetColors(Rainbow(dut.configuration.ledCount, i))

            #print("now: " + str(time.time()) + " timestamp: " + str(time_stamp))
            #print("Time until event: " + str(time_stamp - (time.time_ns() // 1000000)) + "ms")

            group.Send(delayTarget=35) 

            # log measurements
            log_device_stats(group.devices)

            # turn off the led at exactly the next second
            # NOTE: don't use clear command here to simulate a lot of data / even data flow
            group.SetColors([0x000000] * dut.configuration.ledCount)
            group.Send(delayTarget=35) 

            # log measurements
            log_device_stats(group.devices)
    except KeyboardInterrupt:
        pass
    
    group.Disconnect()
    runtime = time.time() - start
    print("\n-------------[Done]-------------")
    print("Total runtime: " + str(time.strftime('%Hh:%Mm:%Ss', time.gmtime(runtime))))
    print("Measurements: " + str(len(sender_times)))
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
        receiver_true_time_drift = GetDrift(sender_times, receiver_out_times[i])
        receiver_estimated_time_drift = GetDrift(sender_times, receiver_time_estimates[i])

        receiver_true_time_slope = GetSlope(sender_times, receiver_out_times[i])

        print("\n Device " + str(i) + " Drift:")
        print(f"True time drift: { receiver_true_time_drift:.10f} s/s or {receiver_true_time_drift * (60*60*24)} s/day")
        print(f"Time drift correction factor: {1/receiver_true_time_slope}")
        print(f"Estimated time drift: {receiver_estimated_time_drift:.10f} s/s or {receiver_estimated_time_drift * (60*60*24)} s/day")

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


def log_device_stats(devices):
    # save current times
    sender_time = (time.time_ns() // 1000000)
    sender_times.append(sender_time)
    group_latencies.append(group.latency)
    for i, device in enumerate(devices):

        time_deltas[i].append(device.time_delta_ms)
        time_deltas_raw[i].append(device._time_delta_ms_raw)

        receiver_time_estimate = device.time_delta_ms + sender_time
        receiver_time_estimates[i].append(receiver_time_estimate)
        receiver_out_times[i].append(device.frame._t_receiver_out)

        # calculate rx and tx latencies (with correction)
        tx_latency = device.frame._t_receiver_in - (device.frame._t_frame_out + device.time_delta_ms)
        rx_latency = (device.frame._t_response_in + device.time_delta_ms) - device.frame._t_receiver_out
        tx_latencies[i].append(tx_latency)
        rx_latencies[i].append(rx_latency)

        # get difference of reported sender out-time to frames time stamp
        timestamp_error = device.frame._t_receiver_out - device.frame.timestamp - device.time_delta_ms
        timestamp_errors[i].append(timestamp_error)

        # get the error of the estimated time to the true time
        time_estimate_error = receiver_time_estimate - device.frame._t_receiver_out
        time_estimate_errors[i].append(time_estimate_error)
        time_estimate_error_corrected = time_estimate_error - rx_latency
        time_estimate_errors_corrected[i].append(time_estimate_error_corrected)

        receiver_packet_processing_times[i].append(device.frame._t_receiver_out - device.frame._t_receiver_in)

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
    fig.suptitle('Group accuracy measurement')

    colors = plt.rcParams["axes.prop_cycle"]()

    text = f'Total runtime: {time.strftime("%Hh:%Mm:%Ss", time.gmtime(runtime))} ({str(len(sender_times))} Measurements) + Time Delta Buffer: {TIME_DELTA_BUFFER_SIZE}'
    for i in range(NUM_DEVICES):
        receiver_true_time_drift = GetDrift(sender_times, receiver_out_times[i])
        receiver_estimated_time_drift = GetDrift(sender_times, receiver_time_estimates[i])
        text += f'\nDev. {str(i)} local time drift:        {receiver_true_time_drift:.10f} s/s or {receiver_true_time_drift*(60*60*24):.5f} s/day\
                 \nDev. {str(i)} corrected time drift: {receiver_estimated_time_drift:.10f} s/s or {receiver_estimated_time_drift*(60*60*24):.5f} s/day'
    
    axes[0].text(0.05, 0.9, text,
                 horizontalalignment='left',verticalalignment='top',transform = axes[0].transAxes)

    # plot everything relative to sender time 
    # plot time_delta
    for i in range(len(time_deltas)):
        color = next(colors)["color"]
        axes[1].plot(sender_times, time_deltas[i],color=color, label= "Dev. " + str(i) + "Time Delta (median)")
        axes[1].plot(sender_times, time_deltas_raw[i], color=color, alpha=0.5, label = "Dev. " + str(i) + "Time Delta (Raw)")
    
    # reset color cycle
    colors = plt.rcParams["axes.prop_cycle"]()
    # plot local times
    for i in range(len(receiver_time_estimates)):
        color = next(colors)["color"]
        axes[2].plot(sender_times, receiver_time_estimates[i], color=color, label = "Dev. " + str(i) + " time estimate")
        axes[2].plot(sender_times, receiver_out_times[i], color=color, alpha=0.5, label = "Dev. " + str(i) + " time (true)")

    colors = plt.rcParams["axes.prop_cycle"]()
    # plot time stamp error
    for i in range(len(timestamp_errors)):
        color = next(colors)["color"]
        axes[3].plot(sender_times, timestamp_errors[i], color=color, label = "Dev. " + str(i) + " time stamp error")

    colors = plt.rcParams["axes.prop_cycle"]()
    # plot time estimation errors
    for i in range(len(time_estimate_errors)):
        color = next(colors)["color"]
        axes[4].plot(sender_times, time_estimate_errors[i], color=color, alpha=0.3, label = "Dev. " + str(i) + " time est. error")
        axes[4].plot(sender_times, time_estimate_errors_corrected[i], color=color, alpha=0.8, label = "Dev. " + str(i) + " time est. error (corr.)")

    axes[5].plot(sender_times, group_latencies, color=color, label = "Group Latency")


    for i in range(len(receiver_packet_processing_times)):
        color = next(colors)["color"]
        axes[6].plot(sender_times, receiver_packet_processing_times[i], color=color, label = "Dev. " + str(i) + " packet processing")

    for i in range(len(latencies)):
        axes [7 + i].plot(sender_times, rx_latencies[i], color=next(colors)["color"], alpha = 0.5, label = "Dev. " + str(i) + " RX Latency (est.)")
        axes [7 + i].plot(sender_times, tx_latencies[i], color=next(colors)["color"], alpha = 0.5, label = "Dev. " + str(i) + " TX Latency (est.)")
        axes [7 + i].plot(sender_times, latencies[i], color=next(colors)["color"], alpha = 0.9, label = "Dev. " + str(i) + " Latency")
    
    # make all ticks of uneven plot numbers to the right side
    for ax in fig.get_axes()[1::2]:
        ax.yaxis.tick_right()
    # configure all axes to look good

    for ax in fig.get_axes()[1:]:
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
    try:
        main()
    except Exception as e:
        if not process is None: 
            process.terminate()
        raise e