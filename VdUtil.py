import math

class VdUtil:
    ALPHA_MASK = 0xFF << 24

    # Returns a [NumberFormat] of sufficient precision to use for formatting coordinate
    # values given the maximum viewport dimension.
    @classmethod
    def getCoordinateFormat(cls, maxViewportSize: float) -> str:
        exponent = int(math.floor(math.log10(maxViewportSize)))
        fractionalDigits = 4 - exponent
        
        if 0 < fractionalDigits:
            if 6 < fractionalDigits:
                fractionalDigits = 6
            return f'{{:.{fractionalDigits}f}}'
        else:
            return '{:.0f}'

    # Parses a color value in #AARRGGBB format.
    # @param color the color value string
    # @return the integer color value
    @classmethod
    def parseColorValue(cls, color: str) -> int:
        if not color.startswith('#'):
            raise ValueError(f'Invalid color value {color}')

        color_length = len(color)
        if color_length == 7:
            # #RRGGBB
            return int(color[1:], 16) | ALPHA_MASK
        elif color_length == 9:
            # #AARRGGBB
            return int(color[1:], 16)
        elif color_length == 4:
            # #RGB
            v = int(color[1:], 16)
            r = (v >> 8) & 0xF
            g = (v >> 4) & 0xF
            b = v & 0xF
            return (r * 0x110000) | (g * 0x1100) | (b * 0x11) | ALPHA_MASK
        elif color_length == 5:
            # #ARGB
            v = int(color[1:], 16)
            a = (v >> 12) & 0xF
            r = (v >> 8) & 0xF
            g = (v >> 4) & 0xF
            b = v & 0xF
            return (a * 0x11000000) | (r * 0x110000) | (g * 0x1100) | (b * 0x11)
        else:
            return ALPHA_MASK