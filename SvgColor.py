# Methods for converting SVG color values to vector drawable format.
class SvgColor:
    # Color table from <a href="https://www.w3.org/TR/SVG11/types.html#ColorKeywords">Recognized
    # color keyword names</a>.
    colorMap = {
        'aliceblue': '#f0f8ff',
        'antiquewhite': '#faebd7',
        'aqua': '#00ffff',
        'aquamarine': '#7fffd4',
        'azure': '#f0ffff',
        'beige': '#f5f5dc',
        'bisque': '#ffe4c4',
        'black': '#000000',
        'blanchedalmond': '#ffebcd',
        'blue': '#0000ff',
        'blueviolet': '#8a2be2',
        'brown': '#a52a2a',
        'burlywood': '#deb887',
        'cadetblue': '#5f9ea0',
        'chartreuse': '#7fff00',
        'chocolate': '#d2691e',
        'coral': '#ff7f50',
        'cornflowerblue': '#6495ed',
        'cornsilk': '#fff8dc',
        'crimson': '#dc143c',
        'cyan': '#00ffff',
        'darkblue': '#00008b',
        'darkcyan': '#008b8b',
        'darkgoldenrod': '#b8860b',
        'darkgray': '#a9a9a9',
        'darkgrey': '#a9a9a9',
        'darkgreen': '#006400',
        'darkkhaki': '#bdb76b',
        'darkmagenta': '#8b008b',
        'darkolivegreen': '#556b2f',
        'darkorange': '#ff8c00',
        'darkorchid': '#9932cc',
        'darkred': '#8b0000',
        'darksalmon': '#e9967a',
        'darkseagreen': '#8fbc8f',
        'darkslateblue': '#483d8b',
        'darkslategray': '#2f4f4f',
        'darkslategrey': '#2f4f4f',
        'darkturquoise': '#00ced1',
        'darkviolet': '#9400d3',
        'deeppink': '#ff1493',
        'deepskyblue': '#00bfff',
        'dimgray': '#696969',
        'dimgrey': '#696969',
        'dodgerblue': '#1e90ff',
        'firebrick': '#b22222',
        'floralwhite': '#fffaf0',
        'forestgreen': '#228b22',
        'fuchsia': '#ff00ff',
        'gainsboro': '#dcdcdc',
        'ghostwhite': '#f8f8ff',
        'gold': '#ffd700',
        'goldenrod': '#daa520',
        'gray': '#808080',
        'grey': '#808080',
        'green': '#008000',
        'greenyellow': '#adff2f',
        'honeydew': '#f0fff0',
        'hotpink': '#ff69b4',
        'indianred': '#cd5c5c',
        'indigo': '#4b0082',
        'ivory': '#fffff0',
        'khaki': '#f0e68c',
        'lavender': '#e6e6fa',
        'lavenderblush': '#fff0f5',
        'lawngreen': '#7cfc00',
        'lemonchiffon': '#fffacd',
        'lightblue': '#add8e6',
        'lightcoral': '#f08080',
        'lightcyan': '#e0ffff',
        'lightgoldenrodyellow': '#fafad2',
        'lightgray': '#d3d3d3',
        'lightgrey': '#d3d3d3',
        'lightgreen': '#90ee90',
        'lightpink': '#ffb6c1',
        'lightsalmon': '#ffa07a',
        'lightseagreen': '#20b2aa',
        'lightskyblue': '#87cefa',
        'lightslategray': '#778899',
        'lightslategrey': '#778899',
        'lightsteelblue': '#b0c4de',
        'lightyellow': '#ffffe0',
        'lime': '#00ff00',
        'limegreen': '#32cd32',
        'linen': '#faf0e6',
        'magenta': '#ff00ff',
        'maroon': '#800000',
        'mediumaquamarine': '#66cdaa',
        'mediumblue': '#0000cd',
        'mediumorchid': '#ba55d3',
        'mediumpurple': '#9370db',
        'mediumseagreen': '#3cb371',
        'mediumslateblue': '#7b68ee',
        'mediumspringgreen': '#00fa9a',
        'mediumturquoise': '#48d1cc',
        'mediumvioletred': '#c71585',
        'midnightblue': '#191970',
        'mintcream': '#f5fffa',
        'mistyrose': '#ffe4e1',
        'moccasin': '#ffe4b5',
        'navajowhite': '#ffdead',
        'navy': '#000080',
        'oldlace': '#fdf5e6',
        'olive': '#808000',
        'olivedrab': '#6b8e23',
        'orange': '#ffa500',
        'orangered': '#ff4500',
        'orchid': '#da70d6',
        'palegoldenrod': '#eee8aa',
        'palegreen': '#98fb98',
        'paleturquoise': '#afeeee',
        'palevioletred': '#db7093',
        'papayawhip': '#ffefd5',
        'peachpuff': '#ffdab9',
        'peru': '#cd853f',
        'pink': '#ffc0cb',
        'plum': '#dda0dd',
        'powderblue': '#b0e0e6',
        'purple': '#800080',
        'rebeccapurple': '#663399',
        'red': '#ff0000',
        'rosybrown': '#bc8f8f',
        'royalblue': '#4169e1',
        'saddlebrown': '#8b4513',
        'salmon': '#fa8072',
        'sandybrown': '#f4a460',
        'seagreen': '#2e8b57',
        'seashell': '#fff5ee',
        'sienna': '#a0522d',
        'silver': '#c0c0c0',
        'skyblue': '#87ceeb',
        'slateblue': '#6a5acd',
        'slategray': '#708090',
        'slategrey': '#708090',
        'snow': '#fffafa',
        'springgreen': '#00ff7f',
        'steelblue': '#4682b4',
        'tan': '#d2b48c',
        'teal': '#008080',
        'thistle': '#d8bfd8',
        'tomato': '#ff6347',
        'turquoise': '#40e0d0',
        'violet': '#ee82ee',
        'wheat': '#f5deb3',
        'white': '#ffffff',
        'whitesmoke': '#f5f5f5',
        'yellow': '#ffff00',
        'yellowgreen': '#9acd32'
    }

    # Converts an SVG color value to "#RRGGBB" or "#AARRGGBB" format used by vector drawables.
    # The input color value can be "none" and RGB value, e.g. "rgb(255, 0, 0)",
    # "rgba(255, 0, 0, 127)", or a color name defined in
    # <a href="https://www.w3.org/TR/SVG11/types.html#ColorKeywords">Recognized color keyword names
    # </a>.
    #
    # @param svgColorValue the SVG color value to convert
    # @return the converted value, or null if the given value cannot be interpreted as color
    # @throws IllegalArgumentException if the supplied SVG color value has invalid or unsupported
    #     format
    @classmethod
    def colorSvg2Vd(cls, svgColorValue: str) -> str:
        color = svgColorValue.strip()
        if color.startswith("#"):
            # Convert RGBA to ARGB.
            if len(color) == 5:
                return f'#{color[4]}{color[1: 4]}'
            elif len(color) == 9:
                return f'#{color[7]}{color[1: 7]}'
            return color
        if 'none' == color:
            return '#00000000'
        if color.startswith('rgb(') and color.endswith(')'):
            rgb = color[4: -1]
            numbers = rgb.split(',')
            if lend(numbers) != 3:
                raise ValueError(svgColorValue)
            builder = '#'
            for i in range(3):
                component = cls.getColorComponent(numbers[i].strip(), svgColorValue)
                builder += '%02X' % component
            assert len(builder) == 7
            return builder
        if color.startswith("rgba(") and color.endswith(')'):
            rgb = color[5: -1]
            numbers = rgb.split(',')
            if len(numbers) != 4:
                raise ValueError(svgColorValue)
            builder = '#'
            for i in range(4):
                component = cls.getColorComponent(numbers[(i + 3) % 4].strip(), svgColorValue)
                builder += '%02X' % component
            assert len(builder) == 9
            return builder
        return cls.colorMap.get(color.lower())

    @classmethod
    def getColorComponent(cls, colorComponent: str, svgColorValue: str) -> int:
        try:
            if colorComponent.endswith('%'):
                value = float(colorComponent[0: -1])
                return cls.clampColor(math.round(value * 255.0 / 100.0))
            return cls.clampColor(int(colorComponent))
        except Exception as e:
            raise Exception(svgColorValue)

    @classmethod
    def clampColor(cls, val: int) -> int:
        return math.max(0, math.min(255, val))