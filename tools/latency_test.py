import colorsys
import statistics
from timeit import default_timer as timer
from matplotlib import pyplot as plt
import numpy as np
from tqdm import tqdm

from pyalup.Device import Device
from pyalup.Frame import Frame

PORT = "COM11"
BAUD = 115200

MEASUREMENTS = 10000

latencies = []

def main():
    print("ALUP Latency test")
    # connect to the controller
    print("Connecting...")
    dut = Device()
    dut.SerialConnect(PORT, BAUD)
    print("Connected")
    print(dut.configuration)

    # measure latency for full color frames
    for offset in tqdm(range(MEASUREMENTS)):
        # generate frame
        #dut.SetColors(Rainbow(dut.configuration.ledCount, offset))
        dut.SetCommand()
        # send frame and wait for response while measuring time
        start = timer()
        dut.Send()
        end = timer()
        latencies.append((end-start) * 1000) # measure in ms



    dut.Clear()
    dut.Disconnect()
    print("Done")
    print("Results:")
    print("Measurements: " + str(len(latencies)))
    print("Min: %fms, Max: %fms, Mean: %fms,variance: %fms " % (min(latencies), max(latencies), statistics.mean(latencies), statistics.variance(latencies) ))

    # Create plot
    plt.figure(figsize=(8, 4))
    plt.plot(np.linspace(0, MEASUREMENTS, MEASUREMENTS), latencies, label='Latency')

    # Set Y-axis range
    plt.ylim(0, 100)

    # Labels and title
    plt.xlabel('Time (s)')
    plt.ylabel('Latency (ms)')
    plt.title('Latency Measurement')
    plt.legend()
    plt.grid(True)

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