"""A collection of functions generating RGB-Effects.

All effect functions  need to have the signature:
        <description>
        
        Parameters:
        n: size of the returned array
        <more params>: description 
        ...

        Returns:
        return_type: An array containing the effect for n LEDs 

All color inputs and outputs are in hexadecimal format 0xRRGGBB
Use HexToRGB(...) and RGBToHex(...) for conversion if needed
        
For n == 0, an effect should return an empty array: [] 

Allways specify default values for function arguments if possible
"""


# TODO: Create separate git, import as submodule

import math
import colorsys

class effects:
    def __init__(self) -> None:
        pass

    # Example effect:
    @staticmethod
    def SingleColor(n: int, color : int) -> list[int]:
        """Apply the given color to all LEDs
        
        Parameters:
        n: size of the returned array
        color: color to apply to all array elements

        Returns:
        return_type: An array containing the given color n times 
        """
        return [color] * n
    


    @staticmethod
    def Gradient(n: int, *colors) -> list[int]:
        """A gradient over all LEDs from the first to the last LED
        
        Parameters:
        n: size of the returned array
        *colors: positive number of integer color values; 
        The effect will be divided into (len(colors) - 1) sections with gradients 
        to the neighboring colors for each section.
        
        Here, the first color will be at the first LED, the last color at the last LED, 
        and every color inbetween will be distributed evenly on all n leds.
        The sections between two colors will be filled with a gradient.

        Returns:
        return_type: An array containing a gradient of all neighbours in the given colors
        """

        if(len(colors) == 0):
            # at least one color is neede for the gradient effect
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
            return [effects._Average(colors)]

        leds = []

        for i in range(n):
            # divide the leds into equal gradient sections
            sections = len(colors) - 1
            current_color_index = int((i / n) * sections)
            gradient_index = i % math.ceil(n/len(colors))
            # find the led's index in the current section
            
            left_color = colors[current_color_index]
            right_color = colors[current_color_index + 1]
            #leds.append(effects._InterpolateColors(i/(n-1), left_color, right_color))

            interpolation_percentage = gradient_index * sections / n
            leds.append(effects._InterpolateColors(interpolation_percentage, left_color, right_color)) # todo: test this, this does not seem to work as expected (according to unittests)

        return leds



    @staticmethod
    def _InterpolateColors(fraction: float, firstColor, secondColor):
        """Interpolate between the first and second color by the given fraction
        
        Parameters:
        fraction:  the interpolation fraction. 0 for the first color, 1 for the second.
                        Values inbetween for a mix of both colors.
        firstColor: The interpolation color for fraction = 0 in hex format
        lastColor: The interpolation color for fraction = 1 in hex format
        Returns:
        return_type: The interpolated hex color
        """       
        
        # convert the hex color to rgb values
        r1, g1, b1 = effects.HexToRGB(firstColor)
        r2, g2, b2 = effects.HexToRGB(secondColor)

        # interpolate the r ,g and b values
        r3 = int(r1 * (1 - fraction) + r2 * fraction)
        g3 = int(g1 * (1 - fraction) + g2 * fraction)
        b3 = int(b1 * (1 - fraction) + b2 * fraction)

        return effects.RGBToHex(r3, g3, b3)
    


    @staticmethod
    def Rainbow(n, offset = 0, scale = 1.0):
        # BUG: this effect is broken sometimes; returns values which are too big
        # example : Rainbow(10,5,1)
        colors = []
        for i in range(n):
            colors.append(effects._RainbowColor(((i - offset)/n) * scale))
        print("Rainbow colors: " + str(colors))
        return colors
    


    @staticmethod
    def _RainbowColor(i):
        """geneate a single rainbow color
        
        @param i: the hue for the geneated color, in range [0.0, 1.0]
        @return: the 24bit hsv color
        
        """
        # get hsv color as rgb array
        color_array = colorsys.hsv_to_rgb(i, 1.0, 1.0)
        # scale array to range [0,255] and combine to hex color
        color = int(color_array[0] * 255)
        color = color << 8
        color += int(color_array[1] * 255)
        color = color << 8
        color += int(color_array[2] * 255)
        return color



    # convert R/G/B colors in range 0-255 to a single hex value with format 0xrrggbb
    @staticmethod
    def RGBToHex(r, g, b):
        color = r
        color = color << 8
        color += g
        color = color << 8
        color += b
        return color



    # convert a hex color in the format 0xrrggbb to (r,g,b) values in range 0-255
    @staticmethod
    def HexToRGB(hex_color):
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF
        return r,g,b

    @staticmethod
    def _Average(values):
        return sum(values) / len(values)