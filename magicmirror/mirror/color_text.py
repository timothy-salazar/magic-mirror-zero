# !/bin/python
#
# Receives text through a Unix pipe and colors it by wrapping each character
# in ANSI escape characters.
# One flaw in the update_mirror.py script is that, in order for it to correctly
# insert text at a specified column while preserving ANSI formatting, each
# individual character we want to format needs to be formatted separately.
# Thus, if you want the text "Hello World!" to be green, each letter will
# be wrapped in its own ANSI escape characters.
# Read the docstring for the 'break_line_into_characters()' function in
# update_mirror.py for a more in depth explanation.
# This is extremely redundant, and it increases the size of term.txt (and
# therefor the overhead for our little Pi Zero to display the contents of
# term.txt) by a significant margin (especially if there's a lot of formatted
# text). However, it's the compromise I've chosen for now.
# I may revisit it at a later date.

import sys
import argparse
# import math
from utilities.color_tracker import LinearColorTracker

def format_rgb(
        char: str,
        rf: int = 0,
        gf: int = 0,
        bf: int = 0,
        rb: int = 0,
        gb: int = 0,
        bb: int = 0):
    """ Input:
            char: str - the character we want to format.
            rf: int - the red component of the foreground
            gf: int - the green component of the foreground
            bf: int - the blue component of the foreground
            rb: int - the red component of the background
            gb: int - the green component of the background
            bb: int - the blue component of the background
        Output:
            formatted_string: str - a string wrapped with ASNI escape sequences
                that will cause 'char' to be represented with foreground and
                background colors specified by rf,gf,bf and rb,gb,bb
                respectively
    """
    formatted_string = '\033['
    # This specifies the color for the foreground (i.e., the color of the text)
    # as a set of RGB colors.
    # We're only adding this if necessary so we can avoid adding unnecessary
    # text to our term.txt file.
    if rf or gf or bf:
        formatted_string += f'38;2;{rf};{gf};{bf};'
    # This specifies the color of the background as a set of RGB values
    if rb or gb or bb:
        formatted_string += f'48;2;{rb};{gb};{bb};'
    # This removes the last semicolon from formatted_string.
    # It's just something we need to do so the ANSI sequences will be understood
    formatted_string = formatted_string[:-1]
    # This is the character we're coloring, as well as an escape sequence to
    # reset the terminal's behavior back to normal (otherwise the foreground/
    # backgroung colors would be applied to all the text from here on)
    formatted_string += f'm{char}\033[0m'
    return formatted_string

def format_by_lookup(
        char: str,
        foreground: int = None,
        background: int = None):
    """ Input:
            char: str - the character we want to format
            foreground: int - a number indicating a color in the system's
                256-color lookup table.
                Specifies color to be applied to foreground (text).
            background: int - a number indicating a color in the system's
                256-color lookup table.
                Specifies color to be applied to background.
        Output:
            formatted_string: str - a string wrapped with ASNI escape sequences
                that will cause 'char' to be represented with foreground and
                background colors specified by 'foreground' and 'background'
                respectively.
    """
    formatted_string = '\033['
    # This sets the foreground color (i.e., the color of the text)
    if foreground:
        formatted_string += f'38;5;{foreground};'
    # This sets the background color
    if background:
        formatted_string += f'48;5;{background};'
    # This removes the last semicolon from formatted_string.
    # It's just something we need to do so the ANSI sequences will be understood
    formatted_string = formatted_string[:-1]
    # This is the character we're coloring, as well as an escape sequence to
    # reset the terminal's behavior back to normal (otherwise the foreground/
    # backgroung colors would be applied to all the text from here on)
    formatted_string += f'm{char}\033[0m'
    return formatted_string

def color_text(
        mode: str,
        text: str,
        foreground: tuple or int = None,
        background: tuple or int = None):
    """ Input:
            mode: str - either 'rgb' or 'color_lookup'
            text: str - the text we want to format
            foreground: tuple of ints or int - the color we want to apply to the
                foreground.
                Either a tuple of integers value (if mode is 'rgb'), or an
                integer corresponding to a color in the system's 256-color
                lookup table (if mode is 'color_lookup)
            background: tuple of ints or int - the color we want to apply to the
                background.
        Output:
            formatted_text: str - the text specified by 'text', formatted with
                the foreground and/or background colors specified by the user.

    Note that there will be a newline at the end of formatted_text, even if the
    user provided a string containing no newlines. This isn't an issue for
    values passed to update_mirror.py, but it might cause problems if you're
    writing other functions and you don't expect the behavior.
    """
    formatted_text = ''
    if mode == 'rgb':
        rf, gf, bf = tuple(foreground) if foreground else (0, 0, 0)
        rb, gb, bb = tuple(background) if background else (0, 0, 0)
        for line in text.split('\n'):
            for char in line:
                formatted_text += format_rgb(char, rf, gf, bf, rb, gb, bb)
            formatted_text += '\n'

    elif mode == 'color_lookup':
        for line in text.split('\n'):
            for char in line:
                formatted_text += format_by_lookup(char, foreground, background)
            formatted_text += '\n'
    return formatted_text

def apply_gradient(
        text: str,
        foreground: LinearColorTracker,
        background: LinearColorTracker
        ):
    """ Input:
            text: str - the text we want to apply formatting to.
            foreground: LinearColorTracker - the color tracker that's handling
                the foreground. Will apply the horizontal and/or vertical
                gradients that were specified by the user, while keeping the
                magnitude within valid range.
            backgorund: LinearColorTracker - the color tracker that's handling
                the background.
        Output:
            formatted_text: str - the text specified by 'text', formatted with
                the foreground and/or background that move through the color
                gradient provided by the user
    """
    formatted_text = ''
    for line in text.split('\n'):
        for char in line:
            formatted_text += format_rgb(
                char,
                *foreground.__next__(),
                *background.__next__(),
                )
        foreground.newline()
        background.newline()
        formatted_text += '\n'
    return formatted_text

def gradient(
        text,
        foreground: tuple = None,
        background: tuple = None,
        h_foreground_increment: tuple = None,
        v_foreground_increment: tuple = None,
        h_background_increment: tuple = None,
        v_background_increment: tuple = None,
        foreground_min_val: tuple = None,
        foreground_max_val: tuple = None,
        background_min_val: tuple = None,
        background_max_val: tuple = None,
        bounce: bool = False
        ):
    """ Input:
            text: str - the text we want to apply formatting to.
            foreground: tuple of 3 ints - the initial values of the red, green,
                and blue components of the foreground.
            background: tuple of 3 ints - the initial values of the red, green,
                and blue components of the background.
            h_foreground_increment: tuple of 3 ints - the amount by which the 
                red, green, and blue components of the foreground should be 
                incremented for each column.
            v_foreground_increment: tuple of 3 ints - the amount by which the 
                red, green, and blue components of the foreground should be 
                incremented for each row.
            h_background_increment: tuple of 3 ints - the amount by which the 
                red, green, and blue components of the background should be 
                incremented for each column.
            v_background_increment: tuple of 3 ints - the amount by which the 
                red, green, and blue components of the background should be 
                incremented for each row.
            foreground_min_val: tuple of 3 ints - the smallest magnitude that
                we want the red, green, and blue components of the foreground to
                be able to reach.
            background_min_val: tuple of 3 ints - the smallest magnitude that
                we want the red, green, and blue components of the background to
                be able to reach.
            foreground_max_val: tuple of 3 ints - the largest magnitude that
                we want the red, green, and blue components of the foreground to
                be able to reach.
            background_max_val: tuple of 3 ints - the largest magnitude that
                we want the red, green, and blue components of the background to
                be able to reach.
            bounce: bool - if False, when the magnitude of a color component
                reaches min_val or max_val, it will stay there. If True,
                the color component will "bounce off the wall", and the
                magnitude of the color component will begin to move in the
                opposite direction
        Output:
            returns the text with the gradient specified applied to the
            foreground and/or the background, in the horizontal and/or vertical
            direction.
    """
    foreground_gradient = LinearColorTracker(
        foreground,
        h_foreground_increment,
        v_foreground_increment,
        foreground_min_val,
        foreground_max_val,
        bounce
    )
    background_gradient = LinearColorTracker(
        background,
        h_background_increment,
        v_background_increment,
        background_min_val,
        background_max_val,
        bounce
    )
    formatted_text = apply_gradient(
        text,
        foreground_gradient,
        background_gradient
    )
    return formatted_text

##
# I may come back to this at some point, but I don't think the returns are
# worth the additional complexity
## 
# def cycle_gradient(step, period, min_value, max_value, offset):
#     """ Input:
#             step: int - the current step of the row or column (depending on
#                 whether this is being used for a vertical or horizontal
#                 gradient)
#             period: int - the number of steps before we finish one complete
#                 cycle of the sine wave.
#             min_value: int - the minimum value allowed for 'out'
#             max_value: int - the maximum value allowed for 'out'
#             offset: int or float - the amount, in units of pi/2, by which the
#                 sine wave we're generating should be shifted to the left. Some
#                 sample values:
#                     offset = 0:
#                         - step=0:           out=max_value       out heading down
#                         - step=(period/2):  out=min_value       out heading up
#                         - step=(period):    out=max_value       out heading down
#                     offset = 1:
#                         - step=0:           out=max_value/2     out heading down
#                         - step=(period/2):  out=max_value/2     out heading up
#                     offset = 2:
#                         - step=0:           out=min_value       out heading up
#                         - step=(period/2):  out=max_value       out heading down
#                     offset = 3:
#                         - step=0:           out=max_value/2     out heading up
#                         - step=(period/2):  out=max_value/2     out heading down
#         Output:
#             out: int - the value of a sine wave with a period of 'period' steps,
#                 whose values fall between 'max_value' and 'min_value', for
#                 step = 'step'
#     """
#     period_term = (math.pi*2*(1/period))
#     h_offset = (math.pi/2)*(offset+1)
#     amplitude = ((max_value - min_value)/2)
#     v_offset = ((max_value + min_value)/2)

#     out = int((math.sin((period_term * step) + h_offset))*amplitude + v_offset)
#     return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # In the future I might make it possible to specify rgb_mode for background
    # and color_lookup mode for foreground (or vice versus), but for now it's
    # one or the other
    # TODO: add styling options (bold, italics, etc.)
    parser.add_argument(
        '-c',
        '--color-lookup',
        help='''
        Sets the program to "color_lookup" mode.
        In this mode foreground and background colors are to be specified by
        a number in the system's 256-color lookup table.
        See:
        https://en.wikipedia.org/wiki/ANSI_escape_code#3-bit_and_4-bit
        ''',
        action='store_true'
    )
    parser.add_argument(
        '-f'
        '--foreground',
        help='''
        The color which should be applied to the foreground. In the default RGB
        mode, this expects three integers in the range 0-255:
        i.e. --foreground 100 200 0
        ''',
        dest='foreground',
        nargs=3,
        type=int)
    parser.add_argument(
        '-b'
        '--background',
        help='''
        The color which should be applied to the foreground. In the default RGB
        mode, this expects three integers in the range 0-255:
        i.e. --background 0 75 200
        ''',
        dest='background',
        nargs=3,
        type=int)
    subparsers = parser.add_subparsers(dest='grad')

    ##################
    # Linear gradient:
    ##################
    grad = subparsers.add_parser(
        'gradient',
        aliases=['grad', 'g'],
    )

    grad.add_argument(
        '-fih',
        '--fg-inc-horiz',
        dest='h_foreground_increment',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the amount by which the red,
        green, and blue components of the foreground should be incremented for
        each column in the text
        '''
    )
    grad.add_argument(
        '-bih',
        '--bg-inc-horiz',
        dest='h_background_increment',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the amount by which the red,
        green, and blue components of the background should be incremented for
        each column in the text
        '''
    )
    grad.add_argument(
        '-fiv',
        '--fg-inc-vert',
        dest='v_foreground_increment',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the amount by which the red,
        green, and blue components of the foreground should be incremented
        for each row in the text
        '''
    )
    grad.add_argument(
        '-biv',
        '--bg-inc-vert',
        dest='v_background_increment',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the amount by which the red,
        green, and blue components of the background should be incremented
        for each row in the text
        '''
    )
    grad.add_argument(
        '-fmin',
        '--fg-min-values',
        dest='fg_min_values',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the minimum values for the red,
        green, and blue components of the foreground
        '''
    )
    grad.add_argument(
        '-bmin',
        '--bg-min-values',
        dest='bg_min_values',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the minimum values for the red,
        green, and blue components of the background
        '''
    )
    grad.add_argument(
        '-fmax',
        '--fg-max-values',
        dest='fg_max_values',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the maximum values for the red,
        green, and blue components of the foreground
        '''
    )
    grad.add_argument(
        '-bmax',
        '--bg-max-values',
        dest='bg_max_values',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the maximum values for the red,
        green, and blue components of the background
        '''
    )
    args = parser.parse_args()
    # print('\n', '-'*20, '\n', args)
    
    intext = sys.stdin.read()
    if args.grad:
        ftext = gradient(
            intext,
            args.foreground,
            args.background,
            args.h_foreground_increment,
            args.v_foreground_increment,
            args.h_background_increment,
            args.v_background_increment,
            args.fg_min_values,
            args.fg_max_values,
            args.bg_min_values,
            args.bg_max_values
        )
    elif not args.color_lookup:
        ftext = color_text('rgb', intext, args.foreground, args.background)
    else:
        ftext = color_text('color_lookup', intext,
                            args.foreground, args.background)

    sys.stdout.write(ftext)
