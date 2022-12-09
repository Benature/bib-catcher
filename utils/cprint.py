from enum import Enum

Color = Enum(
    'Color',
    ('gray', 'red', 'green', 'yellow', 'blue', 'purple', 'cyan', 'white'))

Style = Enum(
    'Style',
    ('default', 'bright', 'faded', 'italic', 'underline', 'negative', 'none'))

Background = Enum(
    'Background',
    ('red', 'green', 'yellow', 'blue', 'purple', 'cyan', 'gray', 'none'))

color_dict = {
    Color.gray: "30",
    Color.red: "31",
    Color.green: "32",
    Color.yellow: "33",
    Color.blue: "34",
    Color.purple: "35",
    Color.cyan: "36",
    Color.white: "37",
}

style_dict = {
    Style.default: "0",
    Style.bright: "1",
    Style.faded: "2",
    Style.italic: "3",
    Style.underline: "4",
    Style.negative: "7",
    Style.none: "8",
}

background_dict = {
    Background.red: "41",
    Background.green: "42",
    Background.yellow: "43",
    Background.blue: "44",
    Background.purple: "45",
    Background.cyan: "46",
    Background.gray: "47",
    Background.none: "48",
}


def get_cprint_format(color=None, style=Style.bright, background=None):
    s = style_dict[style]
    prefix = f"\033[{s}"
    if color is not None:
        c = color_dict[color]
        prefix += f";{c}"
    if background is not None:
        b = background_dict[background]
        prefix += f";{b}"
    prefix += "m"

    suffix = "\033[0m"
    return prefix + "{}" + suffix