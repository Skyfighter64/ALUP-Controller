"""
effects.py

Provides a collection of static RGB effects for LEDs.

Effects are functions which generate a static color effect for LEDs.



--------------------------------------------------
            Adding new Effects
--------------------------------------------------

Create a new module function with the name of the 
effect as function name. 

It needs to take at least one argument n and return 
an array of size n containing hexadecimal RGB color values.

Additional Parameters:
It is possible to define additional parameters for an effect in case n is not
enough. It is recommended to specify a default value for all extra parameters used.

To provide help to end users, add a docstring to effect functions.


--------------------------------------------------
                    Notes
--------------------------------------------------
- All color inputs and outputs are in hexadecimal format 0xRRGGBB
- Use _HexToRGB(...) and _RGBToHex(...) for conversion if needed      
- For n == 0, an effect should return an empty array: [] 
- Specify default values for function arguments if possible

"""


import math
import colorsys

# Example effect:

def SingleColor(n: int, color : int) -> list[int]:
    """Apply the given color to all LEDs
    
    Parameters:
    n: size of the returned array
    color: color to apply to all array elements as hex value: 0xRRGGBB
           Examples: 0xff0000: red, 0x00ff00: green, 0x0000ff: blue

    Returns:
    return_type: An array containing the given color n times 
    """
    return [color] * n
    


def Gradient(n: int, *colors) -> list[int]:
    """A gradient over all LEDs from the first to the last LED
    
    Parameters:
    n: size of the returned array
    *colors: positive number of integer color values; 
    The effect will be divided into (len(colors) - 1) sections with gradients 
    to the neighboring colors for each section.
    
    Here, the first color will be at the first LED, the last color at the last LED, 
    and every color in between will be distributed evenly on all n leds.
    The sections between two colors will be filled with a gradient.

    Returns:
    return_type: An array containing a gradient of all neighbors in the given colors
    """

    if(len(colors) == 0):
        # at least one color is needed for the gradient effect
        # return only black color
        return [0] * n
    if(len(colors) == 1):
        # only one color given, impossible to create gradient
        # return just the given color
        return [colors[0]] * n

    # zero length always returns empty array
    if(n == 0):
        return []
    # too small array, mix all colors
    if(n == 1):
        return [_Average(colors)]

    leds = []

    for i in range(n):
        # divide the leds into equal gradient sections
        sections = len(colors) - 1
        current_color_index = int((i / n) * sections)
        gradient_index = i % math.ceil(n/sections)
        # find the led's index in the current section
        
        left_color = colors[current_color_index]
        right_color = colors[current_color_index + 1]

        #leds.append(effects._InterpolateColors(i/(n-1), left_color, right_color))

        interpolation_percentage = gradient_index * sections / (n-1)
        print("left %d right %d, sections %d, i %d, n %d, gradient_index %d, percentage %f" % (left_color, right_color, sections, i, n,  gradient_index, interpolation_percentage))
        leds.append(_InterpolateColors(interpolation_percentage, left_color, right_color)) # todo: test this, this does not seem to work as expected (according to unittests)

    return leds


def _InterpolateColors(fraction: float, firstColor, secondColor):
    """Interpolate between the first and second color by the given fraction
    
    Parameters:
    fraction:  the interpolation fraction. 0 for the first color, 1 for the second.
                    Values in between for a mix of both colors.
    firstColor: The interpolation color for fraction = 0 in hex format
    secondColor: The interpolation color for fraction = 1 in hex format
    Returns:
    return_type: The interpolated hex color
    """       
    
    # convert the hex color to rgb values
    r1, g1, b1 = _HexToRGB(firstColor)
    r2, g2, b2 = _HexToRGB(secondColor)

    # interpolate the r, g and b values
    r3 = int(r1 * (1 - fraction) + r2 * fraction)
    g3 = int(g1 * (1 - fraction) + g2 * fraction)
    b3 = int(b1 * (1 - fraction) + b2 * fraction)

    return _RGBToHex(r3, g3, b3)



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


def Christmas(n):
    """
    Generate red and green christmas lights
    Parameters:
    n: size of the returned RGB array (number of LEDs)

    Returns:
    return_type: An array containing a rainbow effect for n LEDs
    """
    pattern = [0xf71507,0xff6220,0x75ff33,0x33ff04]
    return Repeat(n, pattern)


def Repeat(n, pattern):
    """
    Repeat a pattern until it fills an array of length n
    @param n: the size of the returned array
    @param pattern: an array of hex colors describing the pattern to repeat

    @return: an array containing the pattern repeated with n elements. 
             If the pattern does not fit it is cut off.
    """
    if len(pattern) == 0:
        return []
    return [pattern[i % len(pattern)] for i in range(n)]


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



def _Average(values):
    """Get average color of given hex color array
    @param values: array of hex color values
    @return: linear average hex color
    """
    r = []
    g = []
    b = []
    
    for value in values:
        _r, _g, _b = _HexToRGB(value)
        r.append(_r)
        g.append(_g)
        b.append(_b)

    r_avg = int(sum(r) / len(r))
    g_avg = int(sum(g) / len(g))
    b_avg = int(sum(b) / len(b))

    return _RGBToHex(r_avg, g_avg, b_avg)