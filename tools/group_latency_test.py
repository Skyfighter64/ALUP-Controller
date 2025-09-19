import colorsys
import statistics
from timeit import default_timer as timer
from matplotlib import pyplot as plt
import numpy as np
from tqdm import tqdm
import math
from cycler import cycler

from pyalup.Device import Device
from pyalup.Frame import Frame
from pyalup.Group import Group

"""

Test the group latency without the 
use of timestamps

"""
MEASUREMENTS = 10000

group_latencies = []  #latency of the group
device_latencies = [] #latency of the individual devices

def main():
    print("ALUP Group Latency test")
    # connect to the controller
    print("Connecting...")

    devices = []

    device0 = Device()
    device0.SerialConnect("COM6", 115200)

    device1 = Device()
    device1.TcpConnect("192.168.180.111", 5012)

    device2 = Device()
    device2.TcpConnect("192.168.180.112", 5012)

    device3 = Device()
    device3.TcpConnect("192.168.180.115", 5012)

    device4 = Device()
    device4.TcpConnect("192.168.180.116", 5012)


    devices.append(device0)
    devices.append(device1)
    devices.append(device2)
    devices.append(device3)
    devices.append(device4)

    device_latencies = [[] for _ in devices]


    group = Group()
    for i in range(len(devices)):
        group.Add(devices[i])
    print("Group Configured: \n" + str(group))

    print("Connected")

    # measure latency for full color frames
    for offset in tqdm(range(MEASUREMENTS)):
        # generate frame
        group.SetColors(Rainbow(100, offset))
        group.Send()
        # send frame and wait for response while measuring time
        group_latencies.append(group.latency) # measure in ms

        for i in range(len(devices)):
            device_latencies[i].append(devices[i].latency)



    group.Clear()

    for device in devices:
        device.Disconnect()
    print("Done")

    #
    #   Print out the results
    #

    print("Results:")
    print("Group Measurements: " + str(len(group_latencies)))
    print("Min: %fms, Max: %fms, Mean: %fms, Variance: %fms " % (min(group_latencies), max(group_latencies), statistics.mean(group_latencies), statistics.variance(group_latencies) ))

    print("\n Device Measurements:")
    for i in range(len(devices)):
        device_latency = device_latencies[i]

        print("Device: " + devices[i].configuration.deviceName  + "("+ str(i) +")")
        print("Measurements: " + str(len(device_latency)))
        print("Min: %fms, Max: %fms, Mean: %fms, Variance: %fms " % (min(device_latency), max(device_latency), statistics.mean(device_latency), statistics.variance(device_latency) ))



    #
    #    Plot the results
    #


    # Create grid plot
    #plt.rcParams['figure.constrained_layout.use'] = True
    fig = plt.figure(figsize=(16, 8))

    #bar_ax = fig.add_subplot()
    gs = fig.add_gridspec(math.floor((len(devices)) / 2) + 2, 2, hspace=0, wspace=0)
    #axes = gs.subplots(sharex='all', sharey='all').flat
    axes = gs.subplots().flat
    fig.suptitle('Latency Measurement Results')

    
    # Histograms for all devices and group
    x_ticks_labels = ["", "Group"] + [devices[i].configuration.deviceName  + " ("+ str(i) +")" for i in range(len(devices))]
    
    axes[0].eventplot([group_latencies] + device_latencies, orientation="vertical", colors=[f'C{i}' for i in range(len(device_latencies) + 1)], lineoffsets=[2*i for i in range(len(devices) + 1)], linewidth=0.5)
    axes[0].set_xticklabels(x_ticks_labels)
    axes[0].xaxis.set_ticks_position('top')

    
    # combined plot of all latencies
    axes[1].plot(np.linspace(0, MEASUREMENTS, MEASUREMENTS), group_latencies, label='Group Latency')
    for i in range(len(devices)):
        axes[1].plot(np.linspace(0, MEASUREMENTS, MEASUREMENTS), device_latencies[i], label='Device ' + str(i))


    # plot the group latency
    axes[2].plot(np.linspace(0, MEASUREMENTS, MEASUREMENTS), group_latencies, label = "Group Latency")


    colors = plt.rcParams["axes.prop_cycle"]()
    # cycle through the first color so colors match
    # TODO: there is certainly a better way for this
    next(colors)["color"]

    for i in range(len(devices)):
        # Note: axes[0] is the combined graph, axes[1] is the group latency
        c = next(colors)["color"]
        axes[i+3].plot(np.linspace(0, MEASUREMENTS, MEASUREMENTS), device_latencies[i],color=c, label = devices[i].configuration.deviceName  + " ("+ str(i) +")")



    axes[0].grid()
    axes[0].set_ylabel('Latency (ms)')
    axes[0].set_ylim([-20, 2500])

    # configure all axes to look good
    for ax in fig.get_axes()[1:]:
        ax.label_outer()
        ax.set_xlabel('Packet')
        ax.set_ylabel('Latency (ms)')
        ax.grid()
        ax.legend()
        # share axes with the group plot
        ax.sharex(axes[1])
        ax.sharey(axes[1])
        ax.set_ylim([-20, 2500])
    
    
    fig.tight_layout()
    #fig.show()


    

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