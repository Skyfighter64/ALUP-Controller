import sys
import ast
import cmd

import serial
import serial.tools.list_ports as list_ports


# led effects
import effects
import animator
from inspect import getmembers, isfunction

sys.path.insert(0,'Python-ALUP')
import importlib  

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


class AlupController(cmd.Cmd):
    intro = """
----------------------------------------------------------------------------
          
      ALUP Controller - CLI for basic interfacing with ALUP devices
          
----------------------------------------------------------------------------
Type 'help' for available commands"""
    prompt = ">>> "

    def do_connect(self, args):
        """connect\nconnect [com] [baud]\t:\t Connect to serial device"""
        try:
            # extract com port and baud
            splittedArgs = args.split(" ")
            com_port = splittedArgs[0]
            baud = 115200

            if len(splittedArgs) > 1:
                baud = int(splittedArgs[1])

            # create new ALUP device
            device = Device()
            device.SerialConnect(com_port, baud)
            conn = AlupConnection(device, com_port)
            conn.cmdloop()

        except serial.serialutil.SerialException:
            print("\nError: Could not connect to device: Device not found.\nType \"list\" to list all devices or \"exit\" to return")

    def do_list(self, args):
        """list\t\t\t:\t List available serial devices"""
        ScanForDevices()
    def do_exit(self, args):
        """exit\t\t\t:\t Exit program"""
        return True






class AlupConnection(cmd.Cmd):
    def __init__(self, device : Device,  com_port : str):   
        self.device = device
        self.prompt = "(%s)> " % (com_port)
        super(AlupConnection, self).__init__()
    
    def __del__(self):
        if self.device.connected:
            self.device.Disconnect()

    def do_config(self, args):
        """Print the ALUP configuration of the active device"""
        print(self.device.configuration)
    def do_command(self, args):
        """Command [command]\t:\t Send an ALUP command to the device"""
        # todo: implement
        pass


    def do_set(self, args):
        """set [i] [color]\t:\t Set led with index i to the specified color (Starting at 0).[color] is a hex 0xRRGGBB color value, eg. 0xff00ff"""
        try:
            splittedArgs = args.split(" ")
            led_index = int(splittedArgs[0])
            colors = [int(splittedArgs[1], 16)]
            self.device.SetColors(colors)
            self.device.frame.offset = led_index
            self.device.Send()
        except ValueError:
            print("index/color Values have to be integer")
        except IndexError:
            print("Wrong amount of arguments given. Expected [i : int], [color : int].\n Type 'help set' for more")


    def do_setrange(self, args):
        """setrange [range] [color]\t:\t Set the leds to the given array. All unspecified leds remain unchanged"""
        pass

    def do_repeat(self, args):
        # todo: function to repeat array of colors until end of led strip
        pass

    def do_setall(self, args):
        """setall [color]\t:\t Set all leds to the specified color. [color] is a hex 0xRRGGBB color value, eg. 0xff00ff"""
        try:
            splittedArgs = args.split(" ")
            colors = [int(splittedArgs[0], 16)] * self.device.configuration.ledCount
            self.device.SetColors(colors)
            self.device.Send()
        except ValueError:
            print("color Value has to be integer. Expected [i : int], [color : int].\n Type 'help set' for more")
        except IndexError:
            print("Invalid number of arguments given")


    def do_clear(self, args):
        """Set all LEDs to black"""
        self.device.SetCommand(Command.CLEAR)
        self.device.Send()
        print("Cleared all LEDs")


    def do_effect(self, args):
        """effect [function name] [optional params]\t:\t Apply an effect from the effects.py library. [Function name] is the name of the effect function in effects.py
           effect [function name] help: Print help text (docstring) for the specified effect function from effects.py
           effect l | list : List all available effects from effects.py"""
        splittedArgs = args.split(" ")
        if(len(splittedArgs) <= 0):
            print("No effect specified. Specify an effect function from effects.py or list all effects using \"effect list\"")
            return
        if(splittedArgs[0] == "l"):
            #short for 'list' but without printing the whole docstring for each effect
            ListEffects(verbose=False)
            return
        if(splittedArgs[0] == "list"):
            ListEffects(verbose=True)
            return
        if(len(splittedArgs) > 1 and splittedArgs[1] == "help"):
            EffectHelp(splittedArgs[0])
            return
        # call function from effect library
        # the <n> parameter will be applied automatically
        # example: "effect StaticColors 0xffffff"
        #           "effect Rainbow"
        ApplyEffect(splittedArgs, self.device)
   

    def do_animation(self, args):
        # initialize animator for the device with 10fps
        anim = animator.Animator(self.device, 10)
        print("Playing test animation")
        try:
            anim.Play(animator.blink, 0x0000ff, 1)
        except KeyboardInterrupt:
            print("Ctl + c pressed. Stopping animation.")
            return


    def do_disconnect(self, args):
        """Terminate connection to device without resetting LEDs"""
        self.device.Disconnect()
        print("Disconnected")
        return True


    def do_dc(self, args):
        """alias for 'disconnect'"""
        self.do_disconnect(args)
        return True


    def do_exit(self, args):
        """Set LEDs to black and terminate connection to device"""
        self.device.SetCommand(Command.CLEAR)
        self.device.Send()
        self.device.Disconnect()
        print("Cleared and Disconnected")
        return True
    

#-----------------------------------------------------------------------------
# 
#            Helper functions which are not part of the CLI
#
#-----------------------------------------------------------------------------


# apply an effect from the effects.py module
# the args parameter has to contain the function name of the effect as first argument
# @param args: [<effect function name in effects.py>, <optional parameters for effect>...] where each element is a string
def ApplyEffect(args, device):
    global effects
    try:
        # HACK: allow any function from effects.py to be executed. This 
        # allows maximum flexibility but might be a bad practice
        # Arguments for functions may be specified in args as string array
        # they are converted into python datatypes automatically

        # try to automatically cast string arguments to their respective native types
        castedArgs = [_castString(arg) for arg in args[1:]]

        # get effect function from effects.py by string name
        effect = getattr(effects, args[0])
        # call effect function with args
        colors = effect(device.configuration.ledCount, *castedArgs)
        # send colors to ALUP device
        device.SetColors(colors)
        device.Send()
    except AttributeError:
        print("Error: could not find function '%s' in effects.py" %(args[0]))
    except TypeError as e:
        print("Error: Wrong amount of arguments given for effect '%s'.\nEffect documentation:\n" % str(args[0]))
        print(effect.__doc__)
        print("Note: the first parameter (n) will be auto filled and needs to be ignored for effect commands")
        print("Error Details:")
        print(e)


# print the docstring of the given effect
# @param effectName: the string name of an effect function in effects.py
def EffectHelp(effectName):
    global effects
    # get effect function from effects.py by string name
    effect = getattr(effects, effectName)
    helpText = effect.__doc__ 
    if(helpText is None):
        print("This effect does not provide a docstring for help")
    else:
        print(effect.__doc__)


def ListEffects(verbose=True):
    global effects
    functions = getmembers(effects, isfunction)
    # filter out all private functions
    effect_functions = [function for function in functions if not function[0][0] == '_']
    print("Available Effects:")
    for effect in effect_functions:
        print(effect[0])
        if(not effect[1].__doc__ is None and verbose):
            print("\t" + effect[1].__doc__)
        print()
    print("Use \"effect <effect name> help\" to learn more about an effect and its parameters")



# try to convert the given string to a python datatype depending on its contents 
def _castString(s):
    try:
        # note: even though literal_eval is considered mostly safe, do not use this in unintended places.
        # this is only needed to cast string arguments from the CLI to python parameters for the effects functions.
        return ast.literal_eval(s)
    except ValueError:
        print("Warning: Could not convert value %s into native type; Will be interpreted as string" %(s))
        return s



def ScanForDevices():
    print("Scanning for connected devices")
    ports = list_ports.comports()

    if (len(ports) == 0):
        print("No ports available")
        return []

    #print("Format:\n[%s]:\n\tdesc: %s\n\thw id: %s \n\tserial number: %s\n\tproduct: %s (%s), %s (%s)" % ("name", "device description", "hardware id", "serial number", "product name", "product id", "manufacturer", "vendor id"))
    print("\nAvailable Serial Ports:")
    for port in ports:
        print("[%s]:\n\tdesc: %s\n\thw id: %s \n\tserial number: %s\n\tproduct: %s (%s), %s (%s)" % (port.device, port.description, port.hwid, port.serial_number, port.product, port.pid, port.manufacturer, port.vid))


if __name__ == "__main__":
    #main()
    AlupController().cmdloop()