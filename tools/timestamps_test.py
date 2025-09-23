import time
from tqdm import tqdm
import colorsys
import statistics
import logging

import time
from matplotlib import pyplot as plt
import numpy as np


from pyalup.Device import Device
from pyalup.Frame import Frame


MEASUREMENTS = 5000

# the difference between the set time stamp of a frame
# and the time the ACK was received.
timestamp_errors = []
time_deltas = [] 
time_deltas_raw = []
# median from raw data (vs. from deque)
time_deltas_median = []

sender_times = [] 

tx_latencies = []
# latency for the acknowledgement from being sent from the receiver to being received at the sender
rx_latencies = []

receiver_out_times = [] # time when receiver sent out packets; this is representative for the receiver's internal time with respect to sender_times
latencies = []


def main():
    # enable logging for ALUP
    #logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    print("ALUP Time Stamps Test")
    # connect to the controller
    print("Connecting...")
    dut = Device()
    #dut.SerialConnect("COM6", 115200)
    dut.TcpConnect("192.168.180.112", 5012)
    print("Connected")
    print(dut.configuration)


    # send some frames to get a first calibration for the time offset
    print("Calibrating time delta")
    for i in tqdm(range(100)):
        dut.SetColors([0x000000])
        dut.frame.timestamp = 0
        dut.Send()
        time_deltas_raw.append(dut._time_delta_ms_raw)
        time_deltas_median.append(statistics.median(time_deltas_raw[-100:]))
    print("Done")

    start = time.time()
    for offset in tqdm(range(MEASUREMENTS)):
        # generate frame
        #dut.SetColors(Rainbow(dut.configuration.ledCount, offset))
        dut.SetColors(Rainbow(1, offset))

        # define the time at which we want to apply the frame
        now_ms = time.time_ns() // 1_000_000
        #timestamp = now_ms + 15
        # add the mean tx latency 
        #timestamp = now_ms + (statistics.mean(tx_latencies[-100:]) if len(tx_latencies) > 0 else 0)
        # add the mean of the biggest quartile tx latency
        recent_tx_latencies = tx_latencies[-100:]
        recent_tx_latencies.sort()
        timestamp = now_ms + (statistics.mean(recent_tx_latencies[-25:]) if len(tx_latencies) > 0 else 0)
        
        # set the time stamp (in the local time domain)
        # NOTE: this timestamp is converted to the 
        # receiver's time domain automatically when sent.
        # It requires accurate time calibration, so for the 
        # first few frames it is inaccurate
        dut.frame.timestamp = timestamp

        # send frame and wait for response
        dut.Send()
        sender_time = dut.frame._t_response_in
        # get difference of reported sender out-time to time stamp
        timestamp_error = dut.frame._t_receiver_out - timestamp - dut.time_delta_ms
        timestamp_errors.append(timestamp_error)

        time_deltas.append(dut.time_delta_ms)
        time_deltas_raw.append(dut._time_delta_ms_raw)
        sender_times.append(sender_time)
        # calculate rx/tx latency and adjust for time domain differences
        tx_latencies.append(dut.frame._t_receiver_in - (dut.frame._t_frame_out + dut.time_delta_ms))
        rx_latencies.append((dut.frame._t_response_in + dut.time_delta_ms) - dut.frame._t_receiver_out)
        latencies.append(dut.latency)
        time_deltas_median.append(statistics.median(time_deltas_raw[-100:]))
        


    runtime = time.time() - start
    dut.Clear()
    dut.Disconnect()
    print("\n-------------[Done]-------------")
    print("Measurements: " + str(MEASUREMENTS))
    print("Total runtime: " + str(time.strftime('%Hh:%Mm:%Ss', time.gmtime(runtime))))
    print("throughput: " + str(MEASUREMENTS / runtime) + " frames/s")
    # Print summaries
    print("Time Stamp Errors:")
    PrintSummary(timestamp_errors)



    # Create plot
    fig = plt.figure(figsize=(16, 8))
    plt.rcParams['figure.constrained_layout.use'] = True
    gs = fig.add_gridspec(3, 2, hspace=0, wspace=0)
    axes = gs.subplots().flat
    fig.suptitle('Time Stamp Error Measurement Results')

    colors = plt.rcParams["axes.prop_cycle"]()

    # plot everything relative to sender time 
    axes[0].plot(sender_times, time_deltas, color=next(colors)["color"], label='Time Delta (median 100)')
    axes[1].plot(sender_times, time_deltas_raw[100:], color=next(colors)["color"], label = "Time Delta (Raw)")
    axes[2].plot(sender_times, tx_latencies, color=next(colors)["color"], label = "Sending Latency (Corrected)")
    axes[3].plot(sender_times, rx_latencies, color=next(colors)["color"], label = "Receiving Latency (Corrected)")
    axes[4].plot(sender_times, latencies, color=next(colors)["color"], label = "Latency")
    axes[5].plot(sender_times, timestamp_errors, color=next(colors)["color"], label = "Time Stamp Error")
    

    
    axes[1].yaxis.tick_right()
    axes[3].yaxis.tick_right()
    axes[5].yaxis.tick_right()
    #axes[7].yaxis.tick_right()

    axes[2].set_ylim([-100, 1500])
    axes[3].set_ylim([-100, 1500])
    axes[4].set_ylim([-100, 1500])
    axes[5].set_ylim([-100, 1500])

    axes[3].sharey(axes[2])
    axes[4].sharey(axes[2])
    axes[5].sharey(axes[2])


    # configure all axes to look good
    for ax in fig.get_axes():
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
    return (statistics.median(data_y[-100:]) - statistics.median(data_y[:100])) / (statistics.median(data_x[-100:]) - statistics.median(data_x[:100]))

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