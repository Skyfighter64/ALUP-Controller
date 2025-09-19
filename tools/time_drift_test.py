import time
from tqdm import tqdm
import colorsys
import statistics

import time
from matplotlib import pyplot as plt
import numpy as np

from pyalup.Device import Device
from pyalup.Frame import Frame

"""
This script is to measure the (constant) drift of the internal time on the ALUP Receiver device
and the related timing statistics.

Explanations:
Latency: The total latency of a packet
rx / tx latency: The sending / receiving latency of a packet; Corrected for timing differences using time deltas
time_deltas: The difference from the Sender's local time to the Receiver's local time; This is used for correction of timestamps.

sender_time: The local time on the Sender
receiver_out_times: The local time on the Receiver (Technically the time when the receiver sends the Packet ACK)
receiver_time: The predicted Receiver's local time (using the Sender's time and the time_delta)

Slopes: The slopes of the tracked time stamps in relation to the Sender's time.
        - The Sender's time slope should always be 1.0
        - The Receiver's time slope and the Receiver's Predicted time should be very similar (the closer the better) but don't need to be 1 for good accuracy

Drift: The drifts for the Receiver's true time and the Receiver's predicted time;  Drift = Slope -1


For details on different stats and how time synchronization works, see ALUP Documentation

Notes:
    - all times are in ms
    - Slope calculation is valid starting from 200 measurements
    - A lot of measurements over a long time span should be made (at least 1+ min or 10 000 measurements)
    - Ideally: Do measurements over multiple hours (2 hours or  1 000 000 measurements recommended (depends on communication speed))
"""
# NOTE: 

#MEASUREMENTS = 200000
MEASUREMENTS =  100000

latencies = []

# difference between receiver system time and sender system time
# ideally, this would be constant

# NOTE: as of last commit, the time deltas are already median of 100
time_deltas = []  
time_deltas_median = []
sender_times = [] 
receiver_times = [] # calculated (corrected) receiver time using the time_delta
tx_latencies = []
# latency for the acknowledgement from being sent from the receiver to being received at the sender
rx_latencies = []

receiver_out_times = [] # time when receiver sent out packets; this is representative for the receiver's internal time with respect to sender_times

timestamp_errors = []
# NOTE: the time estimate error does also include the receiving latency
time_estimate_errors = []   


def main():
    print("ALUP Time Drift test")
    # connect to the controller
    print("Connecting...")
    dut = Device()
    #dut.SerialConnect("COM6", 115200)
    dut.TcpConnect("192.168.180.112", 5012)
    print("Connected")
    print(dut.configuration)

    # measure latency for full color frames
    start = time.time()
    for offset in tqdm(range(MEASUREMENTS)):
        # generate frame
        dut.SetColors(Rainbow(dut.configuration.ledCount, offset))
        # send frame and wait for response while measuring time
        dut.Send()

        time_deltas.append(dut._time_delta_ms_raw)
        time_deltas_median.append(dut.time_delta_ms)

        sender_time = (time.time_ns() // 1000000)
        receiver_time = dut.time_delta_ms + sender_time
        sender_times.append(sender_time)
        receiver_times.append(receiver_time)
        receiver_out_times.append(dut._t_receiver_out)

        tx_latencies.append(dut._t_receiver_in - (dut._t_frame_out + dut.time_delta_ms))
        rx_latencies.append((dut._t_response_in + dut.time_delta_ms) - dut._t_receiver_out)

        latencies.append(dut.latency)

        # get difference of reported sender out-time to frames time stamp
        timestamp_error = dut._t_receiver_out - dut.frame.timestamp - dut.time_delta_ms
        timestamp_errors.append(timestamp_error)

        # get the error of the estimated time to the true time
        time_estimate_error = receiver_time - dut._t_receiver_out
        time_estimate_errors.append(time_estimate_error)

    runtime = time.time() - start
    dut.Clear()
    dut.Disconnect()
    print("\n-------------[Done]-------------")

    print("Total runtime: " + str(time.strftime('%Hh:%Mm:%Ss', time.gmtime(runtime))))
    print("Measurements: " + str(MEASUREMENTS))

    print("\nDifference: Receiver vs. Sender time:")
    PrintSummary(time_deltas)
    print("\nMedian Difference (100): Receiver vs. Sender time:")
    PrintSummary(time_deltas_median)
    
    receiver_true_time_slope = GetSlope(sender_times, receiver_out_times)
    receiver_estimated_time_slope = GetSlope(sender_times, receiver_times)

    print("\n\nSlopes:")
    print("Receiver in times slope (receiver true local time): " + str(receiver_true_time_slope))
    print("Receiver time slope (estimated receiver time / corrected): " + str(receiver_estimated_time_slope))
    print("Sender in times slope: " + str(GetSlope(sender_times, sender_times)))

    # calculate drift from slope
    receiver_true_time_drift = receiver_true_time_slope - 1
    receiver_estimated_time_drift = receiver_estimated_time_slope  - 1

    print("\n\nDrift:")
    print(f"Receiver true local time drift: { receiver_true_time_drift:.10f} s/s or {receiver_true_time_drift * (60*60*24)} s/day")
    print(f"Time drift correction factor: {1/receiver_true_time_slope}")
    print(f"Receiver estimated  time drift: {receiver_estimated_time_drift:.10f} s/s or {receiver_estimated_time_drift * (60*60*24)} s/day")
    print("-----------------------------")
    

    



    
    fig = plt.figure(figsize=(16, 8))
    plt.rcParams['figure.constrained_layout.use'] = True
    gs = fig.add_gridspec(5, 2, hspace=0, wspace=0)
    axes = gs.subplots().flat
    fig.suptitle('Time Synchronization Measurement Results')

    colors = plt.rcParams["axes.prop_cycle"]()

    # plot everything relative to sender time 
    axes[0].plot(sender_times, time_deltas, color=next(colors)["color"], label='Time Delta')
    axes[1].plot(sender_times, time_deltas_median, color=next(colors)["color"], label='Time Delta Median (100)')
    axes[2].plot(sender_times, sender_times,color=next(colors)["color"], label = "Sender local Time")
    axes[3].plot(sender_times, receiver_times, color=next(colors)["color"], label = "Receiver local Time (Corrected)")
    axes[4].plot(sender_times, latencies, color=next(colors)["color"], label = "Latency")
    axes[5].plot(sender_times, tx_latencies, color=next(colors)["color"], label = "Sending Latency (Corrected)")
    axes[6].plot(sender_times, rx_latencies, color=next(colors)["color"], label = "Receiving Latency (Corrected)")
    axes[7].plot(sender_times, timestamp_errors,  color=next(colors)["color"], label =" Time stamp error")
    axes[8].plot(sender_times, time_estimate_errors,  color=next(colors)["color"], label =" Time estimate error (uncorrected)") 
    axes[9].text(0.05, 0.9, f'Total runtime: {time.strftime("%Hh:%Mm:%Ss", time.gmtime(runtime))} ({MEASUREMENTS} Packets)\
                 \nReceiver local time drift:        {receiver_true_time_drift:.10f} s/s or {receiver_true_time_drift*(60*60*24):.5f} s/day\
                 \nReceiver corrected time drift: {receiver_estimated_time_drift:.10f} s/s or {receiver_estimated_time_drift*(60*60*24):.5f} s/day',
                 horizontalalignment='left',verticalalignment='top',transform = axes[9].transAxes)

   

    
    axes[1].yaxis.tick_right()
    axes[3].yaxis.tick_right()
    axes[5].yaxis.tick_right()
    axes[7].yaxis.tick_right()
    


    # configure all axes to look good
    for ax in fig.get_axes()[:-1]:
        #ax.label_outer()
        ax.sharex(axes[1])
        #ax.set_xlabel('Packet')
        ax.set_xlabel('system time (ms)')
        ax.set_ylabel('ms')
        ax.grid()
        ax.legend()
    
    fig.tight_layout()
    # Show plot
    plt.show()

def PrintSummary(data):
    """
    Print a summary of a given list of numbers
    """
    print("\tMean: %fms, Variance: %fms\n\t(Min: %fms, Max: %fms, Range: %fms) " % (statistics.mean(data), statistics.variance(data), min(data), max(data), max(data) - min(data) ))

def GetSlope(data_x, data_y):
    median_size = 25 # NOTE: should be an odd value

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