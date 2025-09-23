import time
from tqdm import tqdm
import colorsys
import statistics
from timeit import default_timer as timer
from matplotlib import pyplot as plt
import numpy as np
import cProfile


from pyalup.Device import Device
from pyalup.Frame import Frame

"""

Test script for measuring time synchronization and various time related statistics

"""



# NOTE: all times are in ms

MEASUREMENTS = 1000


latencies = []

# difference between receiver system time and sender system time
# ideally, this would be constant
# NOTE: as of last commit, the time deltas are already median of 100
time_deltas = [] 
median_size = 100
time_deltas_median = []
sender_times = [] 
receiver_times = [] 

# the time it took for the receiver to process the packet
receiver_packet_processing_times = []
# latency from sending the packet from the sender to receiving it on the receiver
# latencies are adjusted for the time difference of both devices
# raw latencies are not yet adjusted for time difference between sender and receiver
tx_latencies = []
tx_latencies_raw = []
# latency for the acknowledgement from being sent from the receiver to being received at the sender
rx_latencies = []
rx_latencies_raw = []

receiver_in_times = []



def main():
    print("ALUP Time Synchronization test")
    # connect to the controller
    print("Connecting...")
    dut = Device()
    dut.SerialConnect("COM6", 115200)
    #dut.TcpConnect("192.168.180.112", 5012)
    print("Connected")
    print(dut.configuration)

    try: 
        # measure latency for full color frames
        for offset in tqdm(range(MEASUREMENTS)):
            # generate frame
            #dut.SetColors(Rainbow(dut.configuration.ledCount, offset))
            dut.SetColors([])
            # send frame and wait for response while measuring time
            dut.Send()

            time_deltas.append(dut.time_delta_ms)

            time_delta_median = statistics.median(time_deltas[-median_size:])

            time_deltas_median.append(time_delta_median)

            receiver_packet_processing_times.append(dut.frame._t_receiver_out - dut.frame._t_receiver_in)

            sender_time = (time.time_ns() // 1000000)
            receiver_time = time_delta_median + sender_time

            sender_times.append(sender_time)
            receiver_times.append(receiver_time)

            tx_latencies.append(dut.frame._t_receiver_in - (dut.frame._t_frame_out + time_delta_median))
            rx_latencies.append((dut.frame._t_response_in + time_delta_median) - dut.frame._t_receiver_out)
            tx_latencies_raw.append(dut.frame._t_receiver_in - dut.frame._t_frame_out)
            rx_latencies_raw.append(dut.frame._t_response_in - dut.frame._t_receiver_out)

            receiver_in_times.append(dut.frame._t_receiver_in)

            latencies.append(dut.latency)
    except KeyboardInterrupt:
        print("Ctl + C pressed, Stopping.")

    dut.Clear()
    dut.Disconnect()
    print("Done")

    print("Results:")
    print("Measurements: " + str(MEASUREMENTS))

    print("\nDifference: Receiver vs. Sender time:")
    PrintSummary(time_deltas)
    print("\nMedian Difference ("+str(median_size)+"): Receiver vs. Sender time:")
    PrintSummary(time_deltas_median)
    print("\nReceiver packet processing delay")
    PrintSummary(receiver_packet_processing_times)

    print("\nSending Latency")
    PrintSummary(tx_latencies)

    print("\nReceiving Latency")
    PrintSummary(rx_latencies)

    print("\n\nSending Latency (RAW)")
    PrintSummary(tx_latencies_raw)
    print("\nReceiving Latency (RAW)")
    PrintSummary(rx_latencies_raw)
    #print("\n\nSlopes:")
    #print("Receiver in times slope (receiver true local time): " + str(GetSlope(sender_times, receiver_in_times)))
    #print("Receiver time slope (estimated receiver time / corrected): " + str(GetSlope(sender_times, receiver_times)))
    #print("Sender in times slope: " + str(GetSlope(sender_times, sender_times)))
    
    
    fig = plt.figure(figsize=(16, 8))
    plt.rcParams['figure.constrained_layout.use'] = True
    gs = fig.add_gridspec(5, 2, hspace=0, wspace=0)
    axes = gs.subplots().flat
    fig.suptitle('Time Synchronization Measurement Results')

    colors = plt.rcParams["axes.prop_cycle"]()

    # plot everything relative to sender time 
    axes[0].plot(sender_times, time_deltas, color=next(colors)["color"], label='Time Delta')
    axes[1].plot(sender_times, time_deltas_median, color=next(colors)["color"], label='Time Delta Median ('+str(median_size)+')')
    axes[4].plot(sender_times, receiver_packet_processing_times, color=next(colors)["color"], label = "Receiver Packet Processing")
    axes[2].plot(sender_times, sender_times,color=next(colors)["color"], label = "Sender local Time")
    axes[3].plot(sender_times, receiver_times, color=next(colors)["color"], label = "Receiver local Time (Corrected)")
    axes[3].plot(sender_times, receiver_in_times, color=next(colors)["color"], label = "Receiver local Time (True)")
    axes[5].plot(sender_times, latencies, color=next(colors)["color"], label = "Latency")
    axes[6].plot(sender_times, tx_latencies, color=next(colors)["color"], label = "Sending Latency (Corrected)")
    axes[7].plot(sender_times, rx_latencies, color=next(colors)["color"], label = "Receiving Latency (Corrected)")
    axes[8].plot(sender_times, tx_latencies_raw, color=next(colors)["color"], label = "Sending Latency (RAW)")
    axes[9].plot(sender_times, rx_latencies_raw, color=next(colors)["color"], label = "Receiving Latency (RAW)")

    axes[6].sharey(axes[5])
    axes[7].sharey(axes[5])

    axes[1].yaxis.tick_right()
    axes[3].yaxis.tick_right()
    axes[5].yaxis.tick_right()
    axes[7].yaxis.tick_right()
    axes[9].yaxis.tick_right()


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
    return (statistics.median(data_y[-10:]) - statistics.median(data_y[:10])) / (statistics.median(data_x[-10:]) - statistics.median(data_x[:10]))

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