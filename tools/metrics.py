import colorsys
import time
from tqdm import tqdm
from pyalup.Device import Device
import logging
import functools
import numpy as np
from matplotlib import pyplot as plt

"""

    A collection of functions to measure a range of ALUP-related metrics 

"""
logger = logging.getLogger(__name__)


class Metrics():
    """
    Class for storing collected metrics for one device
    """
    def __init__(self):
        # total runtime in s
        self.runtime = 0
        # reference time stamps from the local Sender (used as y in most cases)
        self.sender_times = [] 
        # the offset of the local Sender's time to the local time on the ALUP Receiver
        self.time_deltas_raw = []
        # the current median of the last 100 time_delta_ms_raw measurements
        # This is the core component of ALUP time synchronization. Its accuracy directly represents the synchronization quality
        # NOTE: the median size is configured in pyALUP when initializing a device using `_time_delta_buffer_size`
        self.time_deltas = []
        
        # an estimate of the receivers local time calculated using time_deltas
        # NOTE: The closer to the true receiver time, the better the time synchronization
        self.receiver_time_estimates = []   # calculated (estimated) receiver time

        # the local Receiver time when the response for a frame is sent out.
        # (Mostly) representative for the receiver's true local time
        # NOTE: For time synchronization, this represents t_3
        self.receiver_out_times = []   # time when receiver sent out packets; this is representative for the receiver's internal time

        # Sending / Receiving latency estimates
        # NOTE: all estimates are dependent on the time_delta and therefore affected by its error
        self.tx_latencies = []  
        self.rx_latencies = [] 

        # true measured latency
        # NOTE: This is the Device Latency (the time from sending a Frame to receiving ANY Acknowledgement), not the frame latency
        # (time from a sending a frame to receiving ITS OWN Acknowledgement)
        self.latencies = []  

        # true measured round trip time of a frame (from sending to ITS OWN Acknowledgement)
        self.frame_rtts = []

        # the difference of a frame's time stamp vs. the time it is actually applied
        # NOTE: this is also corrected using time_delta_ms
        self.timestamp_errors = []

        # Error of the receiver time estimate, calculated using receiver_out_times as ground truth
        # NOTE: the time estimate error does also include the rx latency
        self.time_estimate_errors = []   
        # time estimate error corrected by the (also estimated!) rx latency
        # This should represent the true error more closely but is also badly affected by time_delta_ms errors (aka. bad time synchronization)
        self.time_estimate_errors_corrected = []    

        # the time it took for the receiver to process the packet
        self.receiver_packet_processing_times = []   

        # the number of currently unanswered frames
        #NOTE: use this to monitor receiver's buffer usage
        self.openResponses = []


def Measure(device:Device,  measurements=10_000):
    """
    Generate a large amount of ALUP-Packages and measure all relevant stats which are needed for
    calculation of further metrics.
    """

    if (logger.level > logging.INFO):
        logger.warning("Active log level is higher than 'INFO'. Results will not be visible")

    # create metrics object to store the logged data in
    metrics = Metrics()

    # register data collection callback to collect data as soon as a frame gets its response
    device._onFrameResponse = functools.partial(log_device_stats, device, metrics)
    
    # send some frames to get a first calibration for the time synchronization
    # This is NEEDED when using time stamps later on
    logger.info("Calibrating time delta")
    device.Calibrate()
    logger.info("Done")

    print(f"Starting to take {measurements} Measurements for device '{device.configuration.deviceName}'.\nTo interrupt, press Ctrl + c.")

    # log the start time
    start = time.time()
    try:
        for i in tqdm(range(measurements)):
            # generate rainbow colors to simulate real RGB data
            device.SetColors(Rainbow(device.configuration.ledCount, i))
            # send data to device
            device.Send() 
            # NOTE: stats are logged automatically using a callback function
    except KeyboardInterrupt:
        logger.warning("Ctl + C Pressed, Stopping")

    metrics.runtime = time.time() - start

    # remove the callback from the device
    device._onFrameResponse = None
    print("\n-------------[Done]-------------")
    print("Total runtime: " + str(time.strftime('%Hh:%Mm:%Ss', time.gmtime(metrics.runtime))))
    print("Measurements: " + str(len(metrics.sender_times)))
    print("-----------------------------")
    return metrics






# @param frame: the frame from which the data is logged
def log_device_stats(device, metrics, frame):
    """
    Callback function used to log metrics
    @param metrics: a Metrics() instance into which the data is saved
    @param frame: the frame for which the data should be collected

    """
    # save current times
    sender_time = (time.time_ns() // 1000000)
    metrics.sender_times.append(sender_time)

    metrics.time_deltas.append(device.time_delta_ms)
    metrics.time_deltas_raw.append(device._time_delta_ms_raw)

    receiver_time_estimate = device.time_delta_ms + sender_time
    metrics.receiver_time_estimates.append(receiver_time_estimate)
    metrics.receiver_out_times.append(frame._t_receiver_out)


    # calculate rx and tx latencies (with correction)
    tx_latency = frame._t_receiver_in - (frame._t_frame_out + device.time_delta_ms)
    rx_latency = (frame._t_response_in + device.time_delta_ms) - frame._t_receiver_out
    metrics.tx_latencies.append(tx_latency)
    metrics.rx_latencies.append(rx_latency)
    metrics.frame_rtts.append(frame._t_response_in - frame._t_frame_out)

    # get difference of reported sender out-time to frames time stamp
    timestamp_error = frame._t_receiver_out - frame.timestamp - device.time_delta_ms
    metrics.timestamp_errors.append(timestamp_error)

    # get the error of the estimated time to the true time
    time_estimate_error = receiver_time_estimate - frame._t_receiver_out
    metrics.time_estimate_errors.append(time_estimate_error)
    time_estimate_error_corrected = time_estimate_error - rx_latency
    metrics.time_estimate_errors_corrected.append(time_estimate_error_corrected)

    metrics.receiver_packet_processing_times.append(frame._t_receiver_out - frame._t_receiver_in)
    metrics.openResponses.append(len(device._unansweredFrames))

    # save true device latency
    metrics.latencies.append(device.latency)



def PrintDrift(metrics):
    """
    Print out the drift of the true and estimated receiver time
    """
    try: 
        receiver_true_time_drift = GetDrift(metrics.sender_times, metrics.receiver_out_times)
        receiver_estimated_time_drift = GetDrift(metrics.sender_times, metrics.receiver_time_estimates)

        receiver_true_time_slope = GetSlope(metrics.sender_times, metrics.receiver_out_times)

        print(f"True time drift: { receiver_true_time_drift:.10f} s/s or {receiver_true_time_drift * (60*60*24)} s/day")
        print(f"Time drift correction factor: {1/receiver_true_time_slope}")
        print(f"Estimated time drift: {receiver_estimated_time_drift:.10f} s/s or {receiver_estimated_time_drift * (60*60*24)} s/day")
    except ZeroDivisionError:
        print("Could not calculate drift. Not enough data points")


def GetDrift(data_x, data_y):
    """
    Calculate the drift based on given time stamps (y in ms) in comparison to reference time stamps (x in ms).
    Practically, this is the derivation from the given y-value's (assumed to be) linear graph
    to the graph of f(x) = x

    """
    return GetSlope(data_x, data_y) - 1

def GetSlope(data_x, data_y):
    median_size = 25

    # get the median and index of the first n values
    start_index, start_median = argmedian(data_y[:median_size])

    # get the median and index of the last n values    
    end_index, end_median = argmedian(data_y[-median_size:])
    
    return (end_median - start_median) / (data_x[-median_size:][end_index] - data_x[:median_size][start_index])


def Plot(device, metrics):
    if (metrics is None):
        return
     # Create plot
    fig = plt.figure(figsize=(16, 8))
    plt.rcParams['figure.constrained_layout.use'] = True
    gs = fig.add_gridspec(4 , 2, hspace=0, wspace=0)
    axes = gs.subplots().flat
    fig.suptitle('Metrics')

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

    color = next(colors)["color"]
    axes[0].plot(metrics.sender_times, metrics.openResponses,color=color, label= "Open Responses (Max. " + str(device.configuration.frameBufferSize) + ")")
    
    # reset color cycle
    #colors = plt.rcParams["axes.prop_cycle"]()

    # plot everything relative to sender time 
    # plot time_delta
    color = next(colors)["color"]
    axes[1].plot(metrics.sender_times, metrics.time_deltas,color=color, label= "Time Delta (median)")
    axes[1].plot(metrics.sender_times, metrics.time_deltas_raw, color=color, alpha=0.5, label =  "Time Delta (Raw)")

    # reset color cycle
    #colors = plt.rcParams["axes.prop_cycle"]()

    # plot local times
    color = next(colors)["color"]
    axes[2].plot(metrics.sender_times, metrics.sender_times , color=color, label = "Local Sender Time")
    axes[2].plot(metrics.sender_times, metrics.receiver_out_times, color=color, label = "Local Receiver Time")

    colors = plt.rcParams["axes.prop_cycle"]()
    # plot time stamp error
    color = next(colors)["color"]
    axes[3].plot(metrics.sender_times, metrics.timestamp_errors, color=color, label = "Time Stamp Error")

    colors = plt.rcParams["axes.prop_cycle"]()
    # plot time estimation errors
    color = next(colors)["color"]
    axes[4].plot(metrics.sender_times, metrics.time_estimate_errors, color=color, alpha=0.3, label = "Estimated Receiver Time Error (Biased)")
    axes[4].plot(metrics.sender_times, metrics.time_estimate_errors_corrected, color=color, alpha=0.8, label = "Estimated Receiver Time Error (Corrected)")

    #axes[5].plot(sender_times[0], group_latencies, color=color, label = "Group Latency")

    color = next(colors)["color"]
    axes[6].plot(metrics.sender_times, metrics.receiver_packet_processing_times, color=color, label = "Packet Processing Time")

    axes[7].plot(metrics.sender_times, metrics.rx_latencies, color=next(colors)["color"], alpha = 0.5, label = "RX Latency (est.)")
    axes[7].plot(metrics.sender_times, metrics.tx_latencies, color=next(colors)["color"], alpha = 0.5, label = "TX Latency (est.)")
    axes[7].plot(metrics.sender_times, metrics.latencies, color=next(colors)["color"], alpha = 0.9, label = "Device Latency")
    axes[7].plot(metrics.sender_times, metrics.frame_rtts, color=next(colors)["color"], alpha = 0.9, label = "Frame RTT")

    # make all ticks of uneven plot numbers to the right side
    for ax in fig.get_axes()[1::2]:
        ax.yaxis.tick_right()

    # configure all axes to look good
    for ax in fig.get_axes():
        #ax.label_outer()
        ax.sharex(axes[1])
        #ax.set_xlabel('Packet')
        ax.set_xlabel('Sender Time (ms)')
        ax.set_ylabel('ms')
        ax.grid()
        ax.legend()

    for ax in fig.get_axes()[4:]:
        ax.set_ylim(bottom=-20) 
    fig.tight_layout()
    # Show plot
    plt.show()

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
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s %(levelname)s]: %(message)s", datefmt="%H:%M:%S")
    # test run
    device = Device()
    device.logger.setLevel(logging.WARNING)
    device.SerialConnect("COM10", 115200)
    metrics = Measure(device)
    PrintDrift(metrics)

