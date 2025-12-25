import sys
import ast
import cmd

import argparse
import logging

import serial
import serial.tools.list_ports as list_ports

from pyalup.Device import Device
from pyalup.Frame import Frame, Command
# import led effects and animations
import effects
import animator

from inspect import getmembers, isfunction

#sys.path.insert(0,'Python-ALUP')
#import importlib  

# import the main ALUP library
#Device = getattr(importlib.import_module("Python-ALUP.src.Device"), "Device")
#from Python-ALUP.src.Device import Device
# import command definitions
#Command = getattr(importlib.import_module("Python-ALUP.src.Frame"), "Command")
#from Python-ALUP.src.Frame import Command
#from Python-ALUP.src.Frame import Frame
#Frame = getattr(importlib.import_module("Python-ALUP.src.Frame"), "Frame")


#
#
#   Program for testing and debugging ALUP devices
#
#


class AlupController(cmd.Cmd):
    intro = """
----------------------------------------------------------------------------
          
      ALUP Controller - CLI for basic interfacing with ALUP devices
          
----------------------------------------------------------------------------
Type 'help' for available commands"""
    prompt = ">>> "

    def __init__(self, completekey = "tab", stdin = None, stdout = None):
        super().__init__(completekey, stdin, stdout)
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)
        

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
            device.SerialConnect(com_port, baud) #todo: this hangs if baud is wrong
            conn = AlupConnection(device, com_port)
            conn.cmdloop()

        except serial.serialutil.SerialException:
            print("\nError: Could not connect to device: Device not found.\nType \"list\" to list all devices or \"exit\" to return")

    def do_tcpconnect(self, args):
        """tcpconnect\nconnect [ip] [port]\t:\t Connect to a remote device via TCP"""
        try:
            # extract com port and baud
            splittedArgs = args.split(" ")
            ip = splittedArgs[0]
            port = 5012

            if len(splittedArgs) > 1:
                port = int(splittedArgs[1])

            # create new ALUP device
            device = Device()
            device.TcpConnect(ip, port)
            conn = AlupConnection(device, ip + ":" + str(port))
            conn.cmdloop()

        except TimeoutError as e:
            print("Could not connect to remote device: Device did not answer (timeout).")
        except ConnectionRefusedError as e:
            print("Connection Refused by remote device.")


    def do_loglevel(self, args):
        """Get or set the log level.
        Usage: loglevel [level]
        @param level: the log level to set. If not given, the currently active log level is printed out.
        Possible log levels:
            NOTSET (0)
            DEBUG (10)
            INFO (20)
            WARNING (30)
            ERROR (40)
            CRITICAL (50)
        """
        # print out the log level
        newLogLevel = args.split(" ")[0]
        logger = logging.root

        if(newLogLevel == ''):
            print("Current loglevel: " + str(logging.getLevelName(logger.getEffectiveLevel())) + " (" + str(logger.getEffectiveLevel()) + ")")
        else:
            # set the new log level
            try:
                logger.setLevel(newLogLevel)
                print("New loglevel: " + str(logging.getLevelName(logger.getEffectiveLevel())) + " (" + str(logger.getEffectiveLevel()) + ")")
            except ValueError:
                print("Unknown Log Level: " + newLogLevel)

    def do_list(self, args):
        """list\t\t\t:\t List available serial devices"""
        ScanForDevices()
    def do_exit(self, args):
        """exit\t\t\t:\t Exit program"""
        return True
    
    def preloop(self):
        # read in and parse any commandline arguments
        parser = argparse.ArgumentParser(
                    prog='Alup-Controller',
                    description='Interface with ALUP devices to control addressable LEDs')  
        parser.add_argument('-p', '--port', action='store')      # option that takes a value
        parser.add_argument('-b', '--baud', action='store', default="115200")  
        parser.add_argument('--debug', action='store_true')  
        args = parser.parse_args()

        # apply the commandline arguments
        if(args.debug):
            logging.root.setLevel(logging.DEBUG)
        if(not args.port is None):
           print("Connecting to port '%s' with baud %s from command line arguments"  % (args.port, args.baud))
           self.do_connect(args=str(args.port) + " " + str(args.baud))

        return super().preloop()






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
        self.device.Clear()
        print("Cleared all LEDs")


    def do_effect(self, args):
        """
        Apply a color effect from effects.py to the LEDs
        Usage:
        effect [function name] [optional params]\t:\t Apply an effect from the effects.py library. [Function name] is the name of the effect function in effects.py
        effect [function name] help: Print help text (docstring) for the specified effect function from effects.py
        effect l | list : List all available effects from effects.py
        """
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
        """
        Apply an animation function from animator.py to the LEDs.
        Press 'Ctl + c' to stop.
        Usage:
        animation [function name] [optional params]\t:\t Apply an animation from the animator.py library. [Function name] is the name of the animation
        animation l | list : List all available animations
        """
        splittedArgs = args.split(" ")
        if(len(splittedArgs) <= 0):
            print("No animation specified. Specify an animation function from animator.py or list all animations using \"animation list\"")
            return
        if(splittedArgs[0] == "l"):
            #short for 'list' but without printing the whole docstring for each effect
            ListAnimations(verbose=False)
            return
        if(splittedArgs[0] == "list"):
            ListAnimations(verbose=True)
            return
        if(len(splittedArgs) > 1 and splittedArgs[1] == "help"):
            AnimationHelp(splittedArgs[0])
            return
        # call function from effect library
        # the <n> parameter will be applied automatically
        # example: "effect StaticColors 0xffffff"
        #           "effect Rainbow"
        ApplyAnimation(self.device, splittedArgs)


    def do_loglevel(self, args):
        """Get or set the log level.
        Usage: loglevel [level]
        @param level: the log level to set (int or string). If not given, the currently active log level is printed out.
        Possible log levels:
            NOTSET (0)
            DEBUG (10)
            INFO (20)
            WARNING (30)
            ERROR (40)
            CRITICAL (50)
        """
        # print out the log level
        newLogLevel = args.split(" ")[0]
        logger = logging.root

        if(newLogLevel == ''):
            print("Current loglevel: " + str(logging.getLevelName(logger.getEffectiveLevel())) + " (" + str(logger.getEffectiveLevel()) + ")")
        else:
            # set the new log level
            try:
                logger.setLevel(newLogLevel)
                print("New loglevel: " + str(logging.getLevelName(logger.getEffectiveLevel())) + " (" + str(logger.getEffectiveLevel()) + ")")
            except ValueError:
                print("Unknown Log Level: " + newLogLevel)
        

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
        self.device.Clear()
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



# apply an animation from the animator.py module
# the args parameter has to contain the function name of the animation as first argument and all non-optional function arguments except n and t.
# For more info see animator.py
# @param args: array of string: [<animation function name in animator.py>, <optional parameters for animation function>...]
def ApplyAnimation(device, args):
    global animator
    try:
        # HACK: allow any function from the animator.py module to be executed. This 
        # allows maximum flexibility but might be a bad practice
        # Arguments for functions may be specified in args as string array
        # they are converted into python datatypes automatically

        # try to automatically cast string arguments to their respective native types
        castedArgs = [_castString(arg) for arg in args[1:]]

        # get animation function from animator.py by string name
        animation = getattr(animator, args[0])
       
        # initialize animator for the device with 10fps
        anim = animator.Animator(device, 30)
        print("Playing animation '%s'" % (animation.__name__))
        try:
            # Play the animation. Note: this function is blocking indefinitely
            anim.Play(animation, *castedArgs)
        except KeyboardInterrupt:
            print("Ctl + c pressed. Stopping animation.")
            return

    except AttributeError:
        print("Error: could not find function '%s' in animator.py" %(args[0]))
    except TypeError as e:
        print("Error: Wrong amount of arguments given for animation '%s'.\nAnimation documentation:\n" % str(args[0]))
        print(anim.__doc__)
        print("Note: the first two parameters (n, t) will be auto filled and need to be ignored for animation functions")
        print("Error Details:")
        print(e)



# provide help by printint the docstring of the given animation
# @param name: the string name of an animation function in animator.py
def AnimationHelp(name):
    global animator
    # get effect function from effects.py by string name
    animation = getattr(animator, name)
    helpText = animation.__doc__ 
    if(helpText is None):
        print("This effect does not provide a docstring for help")
    else:
        print(animation.__doc__)


def ListAnimations(verbose=True):
    global animator
    functions = getmembers(animator, isfunction)
    # filter out all private functions
    animation_functions = [function for function in functions if not function[0][0] == '_']
    print("Available Effects:")
    for animation in animation_functions:
        print(animation[0])
        if(not animation[1].__doc__ is None and verbose):
            print("\t" + animation[1].__doc__)
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
    AlupController().cmdloop()