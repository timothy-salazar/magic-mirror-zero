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

def format_character_rgb(char, rf=0, gf=0, bf=0, rb=0, gb=0, bb=0):
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

def format_character_name(char, foreground=None, background=None):
    """ Input:
            char: str - the character we want to format
            foreground: str or int - either the name of a color or a number
                indicating a color in the system's 256-color lookup table.
                Specifies color to be applied to foreground (text).
            background: str or int - either the name of a color or a number
                indicating a color in the system's 256-color lookup table.
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

def parse_rgb(rgb):
    """ Input:
            rgb: str - a string representing a comma separated list of rgb
                values
        Output:
            returns a tuple of rgb values.
    """
    rgb_split = rgb.split(',')
    rgb_split = [int(i) if i else 0 for i in rgb_split]
    # # the user SHOULD pass us a comma separated list containing exactly three
    # # items, and I feel as though this should probably break loudly if they
    # # don't, but I've included a more forgiving option.
    # if not strict:
    #     # this fixes things if they've included an extra comma
    #     if len(rgb_split) > 3:
    #         if any([i for i in rgb_split[3:]]):
    #             raise ValueError('''
    #             Expected a comma separated list of 3 integers corresponding to 
    #             an RGB value. Be chastised! Repent your sins and pass only valid
    #             inputs to this humble parse_rgb() function!''')
    #     if len(rgb_split) < 3:
    #         pass
    # Checks to see if we've received the correct number of values
    if len(rgb_split) != 3:
        rgb_len = len(rgb_split)
        raise ValueError(f'''
                Expected a comma separated string of 3 integers corresponding to 
                an RGB value. Instead received a comma separated string of 
                {rgb_len} values: {rgb}
                Be chastised! Repent your sins and pass only valid inputs to
                this humble parse_rgb() function!''')
    if not all([i.isdecimal for i in rgb_split]):
        raise ValueError(f'''
                Expected a comma separated string of 3 integers corresponding to
                an RGB value. Some of the values received were not integers:
                {rgb}
                Know that you have trespassed against the dignity of this humble
                parse_rgb() function, which wishes only to receive valid inputs
                that it might do its job well!''')
    return tuple(rgb_split)

# def test_rgb_parser():
#     test_cases = [
#         '0,0,0',
#         ',,0',
#         '7,0',
#         ',,,',
#         '255,255,255'
#         '11'
#     ]
#     expectations = [
#         (0,0,0),
#         (0,0,0),
#         (7,0,0),
#         (0,0,0),
#         (255,255,255),
#         (11,0,0)
#     ]
#     for test_case, expectation in zip(test_cases, expectations):
#         result = parse_rgb(test_case)
#         assert result == expectation

def thing(mode, text, foreground=None, background=None):
    """ Input:
            mode: str - either 'rgb' or 'color_lookup'
            text: str - the text we want to format
            foreground: str - the color we want to apply to the foreground.
                Either a comma separated list integers corresponding to an rgb
                value (if mode is 'rgb'), or a valid color name or an integer
                corresponding to a color in the system's 256-color lookup table
                (if mode is 'color_lookup)
            background: str - the color we want to apply to the background
        Output:
            formatted_text: str - the text specified by 'text', formatted with 
                the foreground and/or background colors specified by the user.
                
    """
    formatted_text = ''
    if mode == 'rgb':
        fore_names = ['rf', 'gf', 'bf']
        back_names = ['rb', 'gb', 'bb']
        vals = dict()
        if foreground:
            vals.update(
                {name:val for name, val in zip(
                    fore_names, parse_rgb(foreground))})
        if background:
            vals.update(
                {name:val for name, val in zip(
                    back_names, parse_rgb(background))})
        
        for line in text.split('\n'):
            for char in line:
                formatted_text += format_character_rgb(char, **vals)
            

    elif mode == 'color_lookup':
        for line in text.split('\n'):
            for char in line:
                pass

    return formatted_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # In the future I might make it possible to specify rgb_mode for background
    # and color_lookup mode for foreground (or vice versus), but for now it's
    # one or the other
    # TODO: add styling options (bold, italics, etc.)
    # TODO: allow FANCY options, like color gradients.
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-r',
        '--rgb-mode',
        help='''
        This is the default behavior of the program. 
        Sets the program to "RGB" mode. Foreground and background colors are to
        be specified as sets of comma separated integers in the range 0-255.
        Valid examples: 
        "0,0,255", ",,255", "0, 0, 255" 
        ''',
        action='store_true')
    group.add_argument(
        '-c',
        '--color-lookup',
        help='''
        Sets the program to "color_lookup" mode. 
        In this mode foreground and background colors are to be specified by 
        either their name or by their number in the system's 256-color lookup
        table. 
        The names that will be recognized by the terminal are limited, and the 
        user shouldn't be overly surprised if they don't work. For a list of 
        probably valid names, see: 
        https://en.wikipedia.org/wiki/ANSI_escape_code#3-bit_and_4-bit
        This also contains a lookup table that you can reference.
        ''',
        action='store_true'
    )
    parser.add_argument(
        '-f'
        '--foreground',
        help='''
        The color which should be applied to the foreground. In the default RGB
        mode, this expects a comma separated list of integers in the range 0-255
        (such as '255,0,100').
        ''',
        type=str)
    parser.add_argument(
        '-b'
        '--background',
        help='''
        The color which should be applied to the background. In the default RGB
        mode, this expects a comma separated list of integers in the range 0-255
        (such as '255,0,100').
        ''',
        type=str)
    ###
    ## I changed my mind, this is a horrible idea.
    ## it's toooooooo sketchy to use 'eval()', even if the user is defining the
    ## string that's gunna be evaluated. It's like using string formatting to
    ## assemble an SQL query
    ## Still a lotta text, so I'll leave this here for this commit in case I
    ## need to copy/paste some of this later for other less sketchy purposes.
    # parser.add_argument(
    #     '-g'
    #     '--gradient-function',
    #     help='''
    #     A function for generating a gradient in the color. 
    #     For each character in the text the user wants to color, the 
    #     gradient_function string will be evaluated. When it is, the following
    #     local variables will be available:
    #         column: int - the number of the column. This is indexed from the 
    #             beginning of the text, so when the first character is processed
    #             'column' will have a value of 0, the second will have a value of
    #             1, and so on. If the text being processed has multiple lines,
    #             the value of 'column' is 0 at the beginning of each line
    #         row: int - the number of the row. This is indexed from the beginning
    #             of the text, so the first row is 0, and so on. 
    #         rf: int - the red component of the foreground
    #         gf: int - the green component of the foreground
    #         bf: int - the blue component of the foreground
    #         rb: int - the red component of the background
    #         gb: int - the green component of the background
    #         bb: int - the blue component of the background
    #     The gradient_function string must evaluate to a tuple of six values: the
    #     red, green, and blue components of the foreground; and the red, green, 
    #     and blue components of the background. 
    #     If any of the values in the resulting tuple are greater than 255, they
    #     will be set to 255.
    #     Similarly, if any values in the resulting tuple are less than 0, they
    #     will be set to zero.
    #     Example: 
    #         # The following gradient function will do nothing:
    #         gradient_function = '{rf},{gf},{bf},{rb},{gb},{bb}'

    #         # This gradient function will 

    #         # This gradient function will make the color of the text cycle 
    #         # through colors in a pretty rainbow fashion from left to right:
    #         gradient_function = 'int(math.fabs(math.sin(.1*{column})*255)), \
    #             int(math.fabs(math.sin(.2*{column}+1)*255)), \
    #                 int(math.fabs(math.sin(.3*{column}+2)*255)), \
    #                     {rb}, {gb}, {bb}'

    #         ^ As you can see, this can be as complicated as you'd like. Right
    #         now this interface is not very user friendly. It's a minimum viable
    #         product that lets me change the color of the text in more 
    #         interesting ways, but the inputs can be large and unwieldy. 
    #         In the future I intend to add some easier to use interfaces.

    #     NOTE: 
    #     This also is horrifically unsafe from a security perspective.
    #     I'm including it here because I'm going to be manually specifying
    #     the gradient_function strings in my config file, but it makes me 
    #     NERVOUS to have it here at all, so it'll probably be axed at some point
    #     ''',
    #     type=str)
    """
    Linear gradient:
        - start value
        - one of:
            - increment
            - stop value
    Linear gradient 2d:
        - start value (x0, y0)
        - one of:
            - increment x, and increment y
            - stop value x, stop value y
    Cycle:
        - start value
        - period
        - 

    """
    args = parser.parse_args()
    if args.rgb_mode:
        pass

    if args.color_lookup:
        pass
    intext = sys.stdin.read()

    sys.stdout.write(intext) 
    