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
import math

def format_rgb(char, rf=0, gf=0, bf=0, rb=0, gb=0, bb=0):
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

def format_by_lookup(char, foreground=None, background=None):
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

# I'm a little sad to murder this function, but by using argparse's
# functionality to require a list of three integers, I can avoid doing a lot
# of this gross validation
#
# def parse_rgb(rgb):
#     """ Input:
#             rgb: str or none - a string representing a comma separated list of
#                 rgb values
#         Output:
#             returns a tuple of rgb values.
#             If 'rgb' was None, this function returns the tuple (0,0,0)
#     """
#     if not rgb:
#         return (0, 0, 0)
#     rgb_split = rgb.split(',')
#     # This is so if the user passes an invalid string, the function breaks in an
#     # informative way.
#     if len(rgb_split) != 3:
#         rgb_len = len(rgb_split)
#         raise ValueError(f'''
#                 Expected a comma separated string of 3 integers corresponding to 
#                 an RGB value. Instead received a comma separated string of 
#                 {rgb_len} values: {rgb}
#                 Be chastised! Repent your sins and pass only valid inputs to
#                 this humble parse_rgb() function!''')
#     if not all([i.isdecimal for i in rgb_split]):
#         raise ValueError(f'''
#                 Expected a comma separated string of 3 integers corresponding to
#                 an RGB value. Some of the values received were not integers:
#                 {rgb}
#                 Know that you have trespassed against the dignity of this humble
#                 parse_rgb() function, which wishes only to receive valid inputs
#                 that it might do its job well!''')
#     rgb_split = [int(i) if i else 0 for i in rgb_split]
#     return tuple(rgb_split)


def color_text(mode, text, foreground=None, background=None):
    """ Input:
            mode: str - either 'rgb' or 'color_lookup'
            text: str - the text we want to format
            foreground: str - the color we want to apply to the foreground.
                Either a comma separated list integers corresponding to an rgb
                value (if mode is 'rgb'), or an integer corresponding to a
                color in the system's 256-color lookup table (if mode is
                'color_lookup)
            background: str - the color we want to apply to the background
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

def cycle_gradient(step, period, min_value, max_value, offset):
    """ Input:
            step: int - the current step of the row or column (depending on
                whether this is being used for a vertical or horizontal
                gradient)
            period: int - the number of steps before we finish one complete
                cycle of the sine wave.
            min_value: int - the minimum value allowed for 'out'
            max_value: int - the maximum value allowed for 'out'
            offset: int or float - the amount, in units of pi/2, by which the
                sine wave we're generating should be shifted to the left. Some
                sample values:
                    offset = 0:
                        - step=0:           out=max_value       out heading down
                        - step=(period/2):  out=min_value       out heading up
                        - step=(period):    out=max_value       out heading down
                    offset = 1:
                        - step=0:           out=max_value/2     out heading down
                        - step=(period/2):  out=max_value/2     out heading up
                    offset = 2:
                        - step=0:           out=min_value       out heading up
                        - step=(period/2):  out=max_value       out heading down
                    offset = 3:
                        - step=0:           out=max_value/2     out heading up
                        - step=(period/2):  out=max_value/2     out heading down
        Output:
            out: int - the value of a sine wave with a period of 'period' steps,
                whose values fall between 'max_value' and 'min_value', for
                step = 'step'
    """
    period_term = (math.pi*2*(1/period))
    h_offset = (math.pi/2)*(offset+1)
    amplitude = ((max_value - min_value)/2)
    v_offset = ((max_value + min_value)/2)

    out = int((math.sin((period_term * step) + h_offset))*amplitude + v_offset)
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                    default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                    default=sys.stdout)
    # In the future I might make it possible to specify rgb_mode for background
    # and color_lookup mode for foreground (or vice versus), but for now it's
    # one or the other
    # TODO: add styling options (bold, italics, etc.)
    # TODO: allow FANCY options, like color gradients.
    # group = parser.add_mutually_exclusive_group()
    # group.add_argument(
    #     '-r',
    #     '--rgb-mode',
    #     help='''
    #     This is the default behavior of the program.
    #     Sets the program to "RGB" mode. Foreground and background colors are to
    #     be specified as sets of comma separated integers in the range 0-255.
    #     Valid examples:
    #     "0,0,255", ",,255", "0, 0, 255"
    #     ''',
    #     action='store_true')
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
        type=str)
    subparsers = parser.add_subparsers()
    ##################
    # Linear gradient:
    ##################
    #   |              |- foreground -| ...
    #   |              |
    #   |- horizontal -|              |- red
    #   |              |- background -|- green
    #   |                             |- blue
    #   |- vertical ---| ...
    #
    linear = subparsers.add_parser(
        'linear-gradient',
        aliases=['linear', 'lg', 'l']
    )
    sublin = linear.add_subparsers()

    ############################
    # Horizontal linear gradient
    ############################
    horizontal = sublin.add_parser(
        'horizontal',
        aliases=['horizontal-gradient', 'horiz', 'hg']
    )
    # If you're reading this, and you know a way to avoid copy/pasting these
    # options over and over again, let me know. pls.
    horizontal.add_argument(
        '-fi',
        '--foreground-increment',
        dest='h_foreground_increment',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the amound by which the red,
        green, and blue components of the foreground should be incremented for
        each column in the text
        '''
    )
    horizontal.add_argument(
        '-bi',
        '--background-increment',
        dest='h_background_increment',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the amound by which the red,
        green, and blue components of the background should be incremented for
        each column in the text
        '''
    )
    ##########################
    # Vertical linear gradient
    ##########################
    vertical = sublin.add_parser(
        'vertical',
        aliases=['vertical-gradient', 'vert', 'vg']
    )
    vertical.add_argument(
        '-fi',
        '--foreground-increment',
        dest='v_foreground_increment',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the amound by which the red,
        green, and blue components of the foreground should be incremented
        for each row in the text
        '''
    )
    vertical.add_argument(
        '-bi',
        '--background-increment',
        dest='v_background_increment',
        nargs=3,
        type=int,
        help='''
        Expects three integers corresponding to the amound by which the red,
        green, and blue components of the background should be incremented
        for each row in the text 
        '''
    )














    ##################
    # Cylic gradient:
    ##################
    #
    # This part of the parser is UGLY because we need to enable the user to
    # specify period, min_value, max_value, and offset for:
    #   - direction (horizontal, vertical)
    #       - foreground vs. background
    #           - color component (r,g,b)
    # This requires a lot of subparsers

    # OK, this is officially gross enough that I'm going to use another library.
    # Click seems cool.
    cyclic = subparsers.add_parser(
        'cyclic-gradient',
        aliases=['cyclic-gradient', 'cg']
    )
    cycsubs = cyclic.add_subparsers()

    # Direction
    cyc_horiz = cycsubs.add_parser(
        'horizontal',
        aliases=['horizontal-gradient', 'horiz', 'hg']
    )
    cyc_vert = cycsubs.add_parser(
        'vertical',
        aliases=['vertical-gradient', 'vert', 'vg']
    )
    subparser_list = []
    parser_list = []
    for parse in [cyc_vert, cyc_horiz]:
        subparser_list.append(parse.add_subparsers())
        parser_list.append(
            subparser_list[-1].add_parser(
                'foreground',
                aliases=['fg']
            )
        )
        parser_list.append(
            subparser_list[-1].add_parser(
                'background',
                aliases=['bg']
            )
        )
    for p in parser_list:
        p.add_argument(
            '-p',
            '--period',
            dest='period',
            nargs=3,
            type=int,
            help='''
            The number of steps required to finish one complete cycle of the 
            sine wave. 
            '''
        )
        p.add_argument(
            '-o',
            '--offset',
            dest='offset',
            nargs=3,
            type=float,
            help='''
            Three floats corresponding to the offset for the red, green, and 
            blue components.
            The amount, in units of pi/2, by which the sine wave we're 
            generating should be shifted to the left. The function is set so 
            that with an offset of 0, the sine wave will begin at its maximum 
            value. If offset is 2, it starts at its minimum value. 
            '''
        )
        p.add_argument(
            '-mv',
            '--min-vals',
            dest='min_vals',
            nargs=3,
            type=int,
            help='''
            Expects three integers corresponding to the smallest value we should
            allow for the red, green, and blue components.
            '''
        )
        p.add_argument(
            '-mx',
            '--max-vals',
            dest='min_vals',
            nargs=3,
            type=int,
            help='''
            Expects three integers corresponding to the smallest value we should
            allow for the red, green, and blue components.
            '''
        )








    # cyclic = subparsers.add_parser(
    #     'cyclic-gradient',
    #     aliases=['cyclic-gradient', 'cg']
    # )
    # cycopts = cyclic.add_subparsers()
    # ############################
    # # Horizontal linear gradient
    # ############################
    # cyc_horiz = cycopts.add_parser(
    #     'horizontal',
    #     aliases=['horizontal-gradient', 'horiz', 'hg']
    # )
    # '''
    #         period: int - the number of steps before we finish one complete
    #             cycle of the sine wave.
    #         min_value: int - the minimum value allowed for 'out'
    #         max_value: int - the maximum value allowed for 'out'
    #         offset: int or float - the amount, in units of pi/2, by which the
    #             sine wave we're generating should be shifted to the left. Some
    #             sample values:
    #                 offset = 0:
    #                     - step=0:           out=max_value       out heading down
    #                     - step=(period/2):  out=min_value       out heading up
    #                     - step=(period):    out=max_value       out heading down
    #                 offset = 1:
    #                     - step=0:           out=max_value/2     out heading down
    #                     - step=(period/2):  out=max_value/2     out heading up
    #                 offset = 2:
    #                     - step=0:           out=min_value       out heading up
    #                     - step=(period/2):  out=max_value       out heading down
    #                 offset = 3:
    #                     - step=0:           out=max_value/2     out heading up
    #                     - step=(period/2):  out=max_value/2     out heading down
    #                     '''
    # cyc_horiz.add_argument(
    #     '-p',
    #     '--period',
    #     dest='period',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     The number of steps required to finish one complete cycle of the sine
    #     wave. 
    #     '''
    # )
    # cyc_horiz.add_argument(
    #     '-o',
    #     '--offset',
    #     dest='offset',
    #     nargs=3,
    #     type=float,
    #     help='''
    #     Three floats corresponding to the offset for the red, green, and blue
    #     components.
    #     The amount, in units of pi/2, by which the sine wave we're generating 
    #     should be shifted to the left. The function is set so that with an
    #     offset of 0, the sine wave will begin at its maximum value. If offset is
    #     2, it starts at its minimum value. 
    #     '''
    # )
    # cyc_horiz.add_argument(
    #     '-mv',
    #     '--min-vals',
    #     dest='min_vals',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     Expects three integers corresponding to the smallest value we should
    #     allow for the red, green, and blue components.
    #     '''
    # )
    # cyc_horiz.add_argument(
    #     '-mx',
    #     '--max-vals',
    #     dest='min_vals',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     Expects three integers corresponding to the smallest value we should
    #     allow for the red, green, and blue components.
    #     '''
    # )



    # cyc_horiz.add_argument(
    #     '-mf',
    #     '--min-foreground-vals',
    #     dest='min_foreground',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     Expects three integers corresponding to the smallest value we should
    #     allow for the red, green, and blue components of the foreground.
    #     '''
    # )
    # cyc_horiz.add_argument(
    #     '-mb',
    #     '--min-background-vals',
    #     dest='min_background',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     Expects three integers corresponding to the smallest value we should
    #     allow for the red, green, and blue components of the background.
    #     '''
    # )
    # cyc_horiz.add_argument(
    #     '-mxf',
    #     '--max-foreground-vals',
    #     dest='max_foreground',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     Expects three integers corresponding to the largest value we should
    #     allow for the red, green, and blue components of the foreground.
    #     '''
    # )
    # cyc_horiz.add_argument(
    #     '-mxb',
    #     '--max-background-vals',
    #     dest='max_background',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     Expects three integers corresponding to the largest value we should
    #     allow for the red, green, and blue components of the background.
    #     '''
    # )
    
    # ##########################
    # # Vertical cyclic gradient
    # ##########################
    # cyc_vert = cycopts.add_parser(
    #     'vertical',
    #     aliases=['vertical-gradient', 'vert', 'vg']
    # )
    # cyc_vert.add_argument(
    #     '-fi',
    #     '--foreground-increment',
    #     dest='foreground_increment',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     Expects three integers corresponding to the amound by which the red,
    #     green, and blue components of the foreground should be incremented
    #     for each row in the text
    #     '''
    # )
    # cyc_vert.add_argument(
    #     '-bi',
    #     '--background-increment',
    #     dest='background_increment',
    #     nargs=3,
    #     type=int,
    #     help='''
    #     Expects three integers corresponding to the amound by which the red,
    #     green, and blue components of the background should be incremented
    #     for each row in the text 
    #     '''
    # )
    # # Linear gradient:
    # #     - start value
    # #     - one of:
    # #         - increment
    # #         - stop value
    # # Linear gradient 2d:
    # #     - start value (x0, y0)
    # #     - one of:
    # #         - increment x, and increment y
    # #         - stop value x, stop value y
    # # Cycle:
    # #     - start value
    # #     - period
    # #     - max value
    # #     - min_value

    args = parser.parse_args()
    print(args)
    intext = args.infile.read()
    if not args.color_lookup:
        ftext = color_text('rgb', intext, args.foreground, args.background)
    else:
        ftext = color_text('color_lookup', intext,
                            args.foreground, args.background)
    args.outfile.write(ftext)
