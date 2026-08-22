import time
import socket
from typing import List
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo

class MyListener(ServiceListener):
    def __init__(self):
        self.devices = []
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        #print(f"Service {name} updated")
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        #print(f"Service {name} removed")
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.devices.append(info)
        #print(f"Service {name} added, service info: {info}")

def ScanForNetworkDevices()-> List[ServiceInfo]:
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_alup._tcp.local.", listener)
    try:
        # scan for 3 seconds
        time.sleep(3)
    finally:
        zeroconf.close()
    return listener.devices

def IPBytesToString(b : bytearray) -> str:
    return socket.inet_ntoa(b)

def GetProtocolString(device : ServiceInfo) -> str:
    return device.type.split("._")[-1].split(".")[0]