import sys
import platform
sys.path.insert(0,'Python-ALUP')
import importlib  
import serial
import serial.tools.list_ports as list_ports
# import the main ALUP library
Device = getattr(importlib.import_module("Python-ALUP.src.Device"), "Device")
#from Python-ALUP.src.Device import Device
# import command definitions
Command = getattr(importlib.import_module("Python-ALUP.src.Frame"), "Command")
#from Python-ALUP.src.Frame import Command
#from Python-ALUP.src.Frame import Frame
Frame = getattr(importlib.import_module("Python-ALUP.src.Frame"), "Frame")


#
#
#   Program for testing and debugging ALUP devices
#
#

"""
Plan:
- scan ports, list all ALUP devices
- ability to manually trigger scan
- connect to devices
- print out configuration
- set all leds to color
- activate effect
- send commands
- disconnect (alt.: via ctl c)

- use timeouts

"""

def main():
    print("""
----------------------------------------------------------------------------
          
      ALUP Controller - Suite for basic interfacing with ALUP devices
          
----------------------------------------------------------------------------""")
    # main loop
    while(True):
        answer = input("> ").strip()
        if(answer.startswith("connect")):
            # read extra arguments
            args = answer.split(" ")[1:]      
            DeviceDialogue(args)
        elif(answer == "list"):
            ScanForDevices()
        elif(answer == "exit"):
            exit()
        elif(answer == "help"):
            print("\n--- Available Commands: ---")
            print("connect\nconnect [com] [baud]\t:\t Connect to serial device")
            print("list\t\t\t:\t List available serial devices")
            print("exit\t\t\t:\t Exit program")
            print()
        else:
            print("Type \"help\" for help")

def DeviceDialogue(args):
    device, com_port = ConnectionDialogue(args)
    # check if a valid connection was established
    if(device is None):
        return
    
    while(True):
        answer = input("%s@%s> " % (device.configuration.deviceName, com_port)).strip()
        answers = answer.split(" ")

        if(answers[0] == "disconnect" or answers[0] == "exit"):
            print("disconnecting from device...")
            if(answers[0] == "exit"):
                device.SetCommand(Command.CLEAR)
                device.Send()
            device.Disconnect()
            print("Disconnected")
            return
        elif(answers[0] == "set" and len(answers) >= 5 ):
            try:
                led_index = int(answers[1])
                # read in rgb colors and make sure they are within 0-255
                r = max(min(int(answers[2]),255),0)
                g = max(min(int(answers[3]),255),0)
                b = max(min(int(answers[4]),255),0)
                # needing to set all other leds manually; Python-ALUP should implement a function to set by index
                colors = [RGBToHex(r,g,b)]
                device.SetColors(colors)
                device.frame.offset = led_index
                device.Send()

            except ValueError:
                print("index/R/G/B Values have to be integer")
        elif(answers[0] == "setall"):
            #todo
            pass
        elif(answers[0] == "setarray"):
            #todo
            pass
        elif(answers[0] == "clear"):
            # needing to set command manually; Python-ALUP should implement a device.Clear() command
            device.SetCommand(Command.CLEAR)
            device.Send()
            print("Sent Clear command")
        elif(answers[0] == "config"): 
            print(device.configuration)

        elif(answer == "help"):
                print("\n--- Available Commands: ---")
                print("config\t\t\t: Print the ALUP configuration of the device")
                print("disconnect\t:\t Terminate connection to device without resetting LEDs")
                print("exit\t\t\t:\t Set LEDs to black and terminate connection to device")
                print("set [i] [R] [G] [B]\t:\t Set led with index i to the specified color (Starting at 0). R/G/B are in range [0-255]")
                print("setall [R] [G] [B]\t:\t Set all leds to the specified color. R/G/B are in range [0-255]")
                print("setarray [array]\t:\t Set the leds to the given array. All unspecified leds remain unchanged")
                print("clear\t\t\t:\t Set all leds to black")
                print("Command [command]\t:\t Send an ALUP command to the device")
                print()
        else:
            print("Type \"help\" for help")


def ConnectionDialogue(args):
    # list available devices
    if (len(args) <= 0):
        ScanForDevices()
    # interact with user to determine com port and baud rate
    while(True):
        # auto fill com port from args if already provided
        if(len(args) >= 1):
            answer = args[0]
        else:
            print("Enter device name to connect to:")
            answer = input("Connect> ").strip()

        if (answer == "list"):
            ScanForDevices()
        elif (answer == "exit"):
            print("Aborting connection dialogue...")
            return None, ""
        
        com_port = answer
        # autofill if baud rate is provided by args
        if(len(args) >= 2):
            baud_str = args[1]
        else:
            print("Enter baud rate:")
            baud_str = input("Connect>baud> ").strip()
        
        # check if args are valid and try to connect
        try:
            baud = int(baud_str)
        except ValueError:
            print(">>> Invalid baud rate. Has to be a positive integer value.\n>>> Type \"list\" to list all devices or \"exit\" to return")
            continue
        try:
            device = Device()
            device.SerialConnect(com_port, baud)
            return device, com_port
        except serial.serialutil.SerialException:
            print("\n>>> Error: Could not connect to device: Device not found.\n>>> Type \"list\" to list all devices or \"exit\" to return")


# convert R/G/B colors in range 0-255 to a single hex value with format 0xrrggbb
def RGBToHex(r,g,b):
    color = r
    color = color << 8
    color += g
    color = color << 8
    color += b
    return color

# convert a hex color in the format 0xrrggbb to (r,g,b) values in range 0-255
def HexToRGB(hex_color):
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    return r,g,b


# options: array of string options which the answer should be from
# error text: text to show the user for invalid answers
def GetAnswer(options, errortext):
    while(True):
        answer = input()
        if(answer.strip() not in options):
            print(errortext)
        else:
            return answer

def ScanForDevices():
    print("Scanning for connected devices")
    ports = list_ports.comports()

    if (len(ports) == 0):
        print("No ports available")
        return []
    
    
    print("Format:\n[%s]:\n\tdesc: %s\n\thw id: %s \n\tserial number: %s\n\tproduct: %s (%s), %s (%s)" % ("name", "device description", "hardware id", "serial number", "product name", "product id", "manufacturer", "vendor id"))
    print("\nAvailable Serial Ports:")
    for port in ports:
        print("[%s]:\n\tdesc: %s\n\thw id: %s \n\tserial number: %s\n\tproduct: %s (%s), %s (%s)" % (port.device, port.description, port.hwid, port.serial_number, port.product, port.pid, port.manufacturer, port.vid))


if __name__ == "__main__":
    main()