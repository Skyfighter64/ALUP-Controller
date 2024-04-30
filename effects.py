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

import colorsys

class effects:
    def __init__(self) -> None:
        pass

    # Example effect:
    @staticmethod
    def SingleColor(n: int, color : int) -> [int]:
        """Apply the given color to all LEDs
        
        Parameters:
        n: size of the returned array
        color: color to apply to all array elements

        Returns:
        return_type: An array containing the given color n times 
        """
        return [color] * n
    


     # Example effect:
    @staticmethod
    def Gradient(n: int, firstColor : int, secondColor : int) -> [int]:
        """A gradient over all LEDs from the first to the last LED
        
        Parameters:
        n: size of the returned array
        firstColor: The gradient start color
        lastColor: The gradient end color

        Returns:
        return_type: An array containing a gradient from firstColor to  lastColor
        """

        # zero length allways returns empty array
        if(n == 0):
            return []
        # too small array, mix both colors 50/50
        if(n == 1):
            return [effects._InterpolateColors_(0.5, firstColor, secondColor)]

        colors = []
        for i in range(n):
            colors.append(effects._InterpolateColors_(i/(n-1), firstColor, secondColor))

        return colors



    @staticmethod
    def _InterpolateColors_(fraction: float, firstColor, secondColor):
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
