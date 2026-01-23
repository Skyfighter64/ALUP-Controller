"""
file containing a collection of utility and conversion functions
"""

import abc
import logging
from pyalup.SerialConnection import SerialConnection
from pyalup.TcpConnection import TcpConnection

class Convert():
    @abc.abstractmethod   
    def rgbToInt(rgb):
        color = 0
        color += rgb[2]
        color += (rgb[1] << 8)
        color += (rgb[0] << 16) 
        return color
    
    @abc.abstractmethod   
    def intToRGB(color):
        b =  color & 255
        g = (color >> 8) & 255
        r = (color >> 16) & 255
        return [r,g,b]
    
    def intColorToHex(color):
        return "0x{0:06x}".format(color)

    @abc.abstractmethod   
    def rgbToHex(r,g,b):
        return "0x{0:02x}{1:02x}{2:02x}".format(Convert.clamp(r), Convert.clamp(g), Convert.clamp(b))

    @abc.abstractmethod   
    def clamp(x): 
        return max(0, min(x, 255))
    

class Utility():
    """
    Utility functionality for ALUP-Related stuff
    """
    @abc.abstractmethod  
    def SetLogLevel(logger : logging.Logger, level):
        """Set the log level.
        Usage: loglevel [level]
        @param level: the log level to set (int or string).
        Possible log levels:
            NOTSET (0)
            PHYSICAL (5)
            DEBUG (10)
            PROTOCOL (15)
            INFO (20)
            WARNING (30)
            ERROR (40)
            CRITICAL (50)
        """
        # set the new log level
        try:
            logger.setLevel(Utility.TryStrToInt(level))
        except ValueError:
            print("Unknown Log Level: " + str(level))

    @abc.abstractmethod  
    def TryStrToInt(text : str):
        """
        Try to convert a given text to an interger.
        If not possible, return the original text

        """
        try:
            return int(text)
        except ValueError:
            return text


    # create an alup Serial connection from a string of connection parameters
    # Format: [PORT]{:[Baud]}
    # Default Baud: 115200
    @abc.abstractmethod  
    def SerialConnectionFromString(parameters : str):
        splitted = parameters.split(':')
        port = splitted[0]
        baud = int(splitted[1]) if len(splitted) > 1 else 115200
        return SerialConnection(port, baud)

    # Parse the serial connection parameters from a string
    # Format: [PORT]{:[Baud]}
    # Default Baud: 115200
    # @returns port, baud
    @abc.abstractmethod  
    def SerialConnectionParametersFromString(parameters : str):
        splitted = parameters.split(':')
        port = splitted[0]
        baud = int(splitted[1]) if len(splitted) > 1 else 115200
        return port, baud

    # create an alup tcp connection from a string of connection parameters
    # Format: [ip]{:[port]}
    # Default port: 5012
    @abc.abstractmethod  
    def TcpConnectionFromString(parameters : str):
        splitted = parameters.split(':')
        ip = splitted[0]
        port = int(splitted[1]) if len(splitted) > 1 else 5012
        return TcpConnection(ip, port)


    # parse the alup tcp connection parameters from a string 
    # Format: [ip]{:[port]}
    # Default port: 5012
    # @returns: ip, port
    @abc.abstractmethod  
    def TcpConnectionParametersFromString(parameters : str):
        splitted = parameters.split(':')
        ip = splitted[0]
        port = int(splitted[1]) if len(splitted) > 1 else 5012
        return ip, port





def test():
    # test rgb to int
    assert Convert.rgbToInt([255,255,255]) == 0xffffff
    assert Convert.rgbToInt([0,255,255]) == 0x00ffff
    assert Convert.rgbToInt([255,0,255]) == 0xff00ff
    assert Convert.rgbToInt([255,255,0]) == 0xffff00

    # test int to rgb
    assert Convert.intToRGB(0xffffff) == [255,255,255]
    assert Convert.intToRGB(0x00ffff) == [0,255,255]
    assert Convert.intToRGB(0xff00ff) == [255,0,255]
    assert Convert.intToRGB(0xffff00) == [255,255,0]

if __name__ == "__main__":
    test()