from pyalup.Device import Device
from pyalup.Frame import Frame
import functools
import time

class PingMetrics():
    """
    Container class for ping metrics used in the frame callback
    """
    def __init__(self):
        self.tx_latency = 0
        self.rx_latency = 0
        self.device_latency = 0
        self.frame_latency = 0

def Ping(device : Device, n = 4, pause = 1000):
    print(f"Pinging {device.configuration.deviceName} {n} times...")
    metrics = PingMetrics()
    device._onFrameResponse = functools.partial(_ping_callback, device, metrics)
    print("Registered Callback")
    for i in range(n):
        try:
            time.sleep(pause/1000)
            frame = Frame()
            frame.timestamp = 0
            device.Send(frame)
            print(f"Response Received. Device Latency: {metrics.device_latency}ms, Frame Latency: {metrics.frame_latency}ms, TX|RX latency: {metrics.tx_latency}ms | {metrics.rx_latency}ms")
        except TimeoutError as e:
            print("Device timed out.")
            print(e)
        except KeyboardInterrupt:
            print("Ctl+C pressed, stopping")
            device.FlushBuffer()
            return

def _ping_callback(device : Device, metrics : PingMetrics, frame):
    metrics.frame_latency = frame._t_response_in - frame._t_frame_out
    metrics.device_latency = device.latency

    # calculate rx and tx latencies (with correction)
    metrics.tx_latency = frame._t_receiver_in - (frame._t_frame_out + device.time_delta_ms)
    metrics.rx_latency = (frame._t_response_in + device.time_delta_ms) - frame._t_receiver_out 

