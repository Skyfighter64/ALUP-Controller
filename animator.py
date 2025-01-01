"""
Animator.py

Provides Animation effects for the LED strip

Animations are just like effects, except instead of returning the same array of colors every time, animations
also get a time parameter t, according to which they may change the color array, creating some kind 
of animation.

Time t is either the length of one frame defined by the FPS parameter or
however long the ALUP controller takes to apply the colors to the LED strip.
The FPS may be capped by the hardware capabilities


--------------------------------------------------
            Adding new Animations
--------------------------------------------------

Create a new module function with the name of the 
Animation as function name. 

Every animation function NEEDS to take in at least two 
arguments n and t and returns an array of hexadecimal 
color values.

n describes the desired size of the returned array of colors
and is most likely the number of LEDs.

t describes the current time step. This is the loop iteration variable
of the Animator.Play function and  will increase by one for every function call from the Animator.
When crating animations you may assume a usual frame rate of 30 FPS


Additional Parameters:
It is possible to define additional parameters for an animation in case n and t are not
enough. When playing an animation, Animator.Play() will pass all extra arguments given 
to the actual Animation function. It is recommended to specify a default value for all 
extra parameters. For an example, see the blink() animation with its extra 'color' parameter

Return value:
An animation needs to return an array of Size n which contains the colors values for depending
on the the given time t

To provide help to end users, add a docstring to animation functions.

--------------------------------------------------
                    Notes
--------------------------------------------------
- All color inputs and outputs are in hexadecimal format 0xRRGGBB
- Use _HexToRGB(...) and _RGBToHex(...) for conversion if needed      
- For n == 0, an animation should return an empty array: [] 
- Specify default values for function arguments if possible



Todo: deltaTime for argument to make it fps / lag independent or scale t in animator with deltatime
make animations stop when empty array is returned


"""
import time
import colorsys
import random

class Animator:
    """
    Animator class providing functionality to
    play animations on the given ALUP device

    """
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
        """
        Play an animation on the ALUP device

        @param animation: the animation function which should be played
        @param *args: any extra arguments which the specified animation may
                      need. Does not include the required arguments n and t
                      for animation functions.
        """
        # the time counter; increases by one with every new frame
        t = 0
        while(True):
            # get the start time of this frame
            start = time.time()
            colors = animation(self.device.configuration.ledCount, t, *args)

            # stop the animation if an empty array is received
            if(len(colors) == 0):
                # clear the leds
                self.device.Clear()
                break

            self.device.SetColors(colors)
            self.device.Send()

            end = time.time()
            # sleep for the time which is missing to hit the requested fps
            time.sleep(max(0, 1/self.fps  - end + start))
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
    

def blink(n,t,color=0xffffff, pause=10):
    """
    Blink the given color every 10 timesteps
    
    color: Hexadecimal integer value defining the color which will blink on all LEDs

    pause: the number of timesteps to pause between switching colors
    """
    if (int(t/pause) % 2 == 0):
        # return the selected color
        return [color] * n
    else:
        # return black color
        return [0x000000] * n
    


def Rainbow(n, t, scale = 1.0):
    """Generate a rainbow effect

    Parameters:
    scale: the scaling factor for the rainbow color. scale < 1.0 stretches all colors while scale > 1.0 compresses them

    Returns:
    return_type: An array containing a rainbow effect for n LEDs
    """
    colors = []
    for i in range(n):
        colors.append(_RainbowColor(((i + t/10)/n) * scale))
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



def Firework(n, t, position = -1, color = 0xff0000):
    """
    This animation is WIP
    """
    if(position < 0):
        # choose random position
        position = round(random() * n)
    if(color < 0):
        # choose random color
        color = _RainbowColor(random())

    """
    plan: 
    - spawn white flash at explosion point
    - make fade from white to color fast after the explosion
    - propagate colored pixel to both sides with certain expansion speed 
    - reduce brightness with time
    - maybe add some noise to the fade down
    """
    if (t < 5):
        return Flash(n, t, position, color)
    else:
        return FadeOut(n, t, LogSpread(n, t, position, color))


def SqrtSpread(n, t, position, color, startSpeed):
    """
    Spread the received color from the given position to both sides, reducing speed quadratically
    """
    # calculate speed based on the current point in time
    speed = startSpeed - (0.1*t)**2
    # the outermost pixel position of the spread
    offset = round(speed * t)

    # initialize all pixels to black
    colors = [0x000000 for i in range(n)]
    print("offset: %d speed: %d" % (offset, speed))
    # make all pixels from the given startPosition +- position have the given color

    # indices of boder pixels
    minIndex = position - offset
    maxIndex = position + offset

    print("min %d , max %d" % (minIndex, maxIndex))

    colors[minIndex : maxIndex] = [color for _ in range(1 + (2* offset))] # todo: this does not quite work, wrong pixels are set
    # cut the ends if they are too big
    colors = colors[0:n]

    # assertion which makes sure the length is right
    assert len(colors) == n

    return colors

def FadeOut(n, t, speed, _colors):
    """
    reduce colors linearly until they are black
    
    """
    # we need to make a copy of the list because we would otherwise
    # cause a loopback 
    # todo is this really needed or could we just modify the existing array
    # would definitely be faster (but problematic for float speeds / rounding error)
    colors = list(_colors)
    # calculate an even reduction for the current point in time
    reduction = max(0, round(speed * t))

    if(reduction >= 255):
        # tell the animator that this animation is finished
        return []

    for i in range(len(colors)):
        # get the led's rgb values from the hex color
        r,g,b = _HexToRGB(colors[i])
        # apply the reduction
        r = max(0, r - reduction)
        g = max(0, g - reduction)
        b = max(0, b - reduction)
        # convert the rgb values back to rgb 
        colors[i] = _RGBToHex(r,g,b)

    return colors


# todo: quadratic fadeout, looks nice but was a bug


# convert R/G/B colors in range 0-255 to a single hex value with format 0xrrggbb
def _RGBToHex(r, g, b):
    color = r
    color = color << 8
    color += g
    color = color << 8
    color += b
    return color



# convert a hex color in the format 0xrrggbb to (r,g,b) values in range 0-255
def _HexToRGB(hex_color):
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    return r,g,b
