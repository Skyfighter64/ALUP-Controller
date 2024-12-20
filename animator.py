"""
Animator.py

Provides Animation effects for the LED strip

Animations are just like effects, except returning the same array of colors every time, animations
also get a time parameter t, according to which they may change the color array, creating some kind 
of animation.

Time t is however long the ALUP controller takes to apply the colors to the LED strip. This may be around 0.03s or faster/slower
Todo: make user-settable FPS

All animation functions need to have the signature:
        <description>
        
        Parameters:
        n: size of the returned array
        t: current time to 
        <more params>: description 
        ...

        Returns:
        return_type: An array containing the colors for the given time t for n LEDs 

All color inputs and outputs are in hexadecimal format 0xRRGGBB
Use _HexToRGB(...) and _RGBToHex(...) for conversion if needed
        
For n == 0, an effect should return an empty array: [] 

Always specify default values for function arguments if possible

All effects should have a python docstring specifying all input parameters.

"""


import time

"""
Plan: make an animator class which can be run in parallel which knows the fps, tracks time and pauses if needed?
- possiblility to merge, split, fade, modify animations,...

Make animations as module functions which have n and t as guaranteed parameters


"""

class Animator:
    def __init__(self, device, fps:float=30):
        """
        Default constructor

        @param device: the ALUP device instance on which the animation should be played.
                       The connection already needs to be established.
        @param fps:  The number of animation time steps taken per second. Note that this factor
                     might be hardware limited by the LEDs, microcontroller or connection type.
                     Range: [0, ...]. If the fps are higher than the microcontroller can handle,
                     the true FPS will just be the maximum possible depending on the hardware.
        """
        self.device = device
        self.fps = fps
        

    def Play(self, animation, *args):
        # the time counter; increases by one with every new frame
        t = 0
        while(True):
            # get the start time of this frame
            start = time.time()

            colors = animation(self.device.configuration.ledCount, t, *args)
            self.device.SetColors(colors)
            self.device.Send()

            end = time.time()
            # sleep for the time which is missing to hit the requested fps
            time.sleep(1/self.fps  - end + start)
            # increase time counter
            t += 1
        
         



def testAnimation(n,t):
    """
    Simple test animation.
    Switches between red and green color every 10 timesteps
    """
    if (int(t/10) % 2 == 0):
        return [0xff0000] * n
    else:
        return [0x00ff00] * n
    

def blink(n,t,color, pause):
    """
    Blink the given color every 10 timesteps
    @param color: Hexadecimal integer value defining the color which will blink on 
    all LEDs
    @param pause: the number of timesteps to pause between switching colors
    """
    if (int(t/pause) % 2 == 0):
        # return the selected color
        return [color] * n
    else:
        # return black color
        return [0x000000] * n