""" Receives block of text from a plugin and inserts the block of text into the
term.txt file.
"""
import os
import sys
import argparse
import re

def get_script_dir():
    """ Input:
            None
        Output:
            script_dir: pathlib.Path - the path of the script directory

    This is just for my paranoia. It gives the path to the directory in which
    this script resides.
    TODO: It probably makes sense to have directory of the entire project stored
    as an environment variable.
    """
    this_file_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(this_file_path)
    return script_dir

def make_term_file():
    """ Input:
            None
        Output:
            Creates or overwrites a file with enough whitespace characters to
            completely fill the terminal.
    This does the following:
        - Gets the terminal width and height (in columns and rows)
        - Opens a file in the same directory as this script named "term.txt"
        - Fills the file with spaces, such that there are term_height lines,
          each of which is term_width long.
    """
    # Width/height are in columns/lines
    term_width, term_height = os.get_terminal_size()
    # This makes a string that should completely cover the terminal if you print
    # it out.
    # Equivalent to:
    #   display_text = ''
    #   for y in range(term_height):
    #       for x in range(term_width):
    #           display_text += ' '
    #       display_text += '\n'
    display_text = '\n'.join([' '*term_width for i in range(term_height)])
    script_dir = get_script_dir()
    term_file_path = os.path.join(script_dir, 'term.txt')
    with open(term_file_path, 'w+') as f:
        f.write(display_text)

def break_line_into_characters(line):
    """ We're going to be using ANSI escape codes to add color to
    characters/background, add styling (bold, underline, etc.), and who knows
    what other shenanigans.
    This adds some complexity to the insert_text_block() function.
    If we didn't use ANSI escape codes, one character in the term.txt file would
    represent one character on the terminal. That would make it pretty trivial
    to insert blocks of text into term.txt, since we could just break the text
    into rows, and then slice each row at (for example) character 5, if we
    wanted to insert text there.
    With ANSI escape codes, we have extra text associated with each character.
    A pink "Z" on a blue background is:
        '\x1b[38;2;200;16;57;48;2;10;6;200mZ\x1b[0m'
    This function takes a string and turns it into a list, where each entry is
    a single printable character.

    ### BIG ASSUMPTION: ###
    For simplicity, we're going to assume that each character with ANSI escape
    code formatting is formatted individually.
    If we want "Hello world!" to be printed in red, we *could* print the
    sequence:
        '\x1b[38;2;255;0;0mHello world!\x1b[0m'
    But instead, we will be printing each individual character in its own escape
    sequence bubble:
        '\x1b[38;2;255;0;0mH\x1b[0m\x1b[38;2;255;0;0me\x1b[0m'...
    This makes the term.txt file VERY VERBOSE, and I'm not sure that it's the
    best way to approach this.
    We're also going to assume that each character is followed by '\x1b[0m',
    which is an escape sequence that resets all attributes (so we have a clean
    slate.
    Given that most of the term.txt file is expected to be whitespace (this is
    for a magic mirror, and most of the display will be blank), I don't think
    that this will have enough of an impact to really matter - but I could be
    wrong. We'll see.
    """

    get_char_expression = r'''
        \x1b\[          # This begins the escape sequence
        ([0-9]{1,3};)+? # semicolon-separated parameters
        [0-9]{1,3}m     # final parameter
        (?P<char>.)     # the printable character
        \x1b\[0m        # resets everything back to normal
        |.              # this matches non-ANSI-formatted characters
        '''
    get_char = re.compile(get_char_expression, re.VERBOSE)
    return [i.group(0) for i in get_char.finditer(line)]

def twiddle_bits(old_str):
    """ Input:
            old_str: string - the text we intent to display on the terminal
        Output:
            twiddled: string - the exact same string, but with a deliberately
                superficial change to the very end.
    This takes the string we're going to print to the terminal and it changes
    the last few characters.
    The ANSI escape sequence '\x1b\[0m' resets all attributes to normal.
        - if the file does not end with '\x1b\[0m', we add it to the end
        - if there is one occurrence of the string, we repeat it
        - if there is more than one occurrence, we replace it with a single
          repetition
    The reason for this is our use of the 'tail' command to display the contents
    of term.txt.
    If you run the command:
        tail +0 -f term.txt
    it will display the contents of term.txt _beautifully_, including all the
    color formatting we get from our ANSI escape sequences. On top of that, it
    will display changes to the file.....
    ...but only if the end of the file has been changed (the documentation says
    that it waits "for additional data to be appended to the input").
    So this isn't exactly what I want, but I'm trying to get a POC first, and
    I'll try to make this *slick* and *cool* later.
    """
    end_codes = re.compile('(\x1b\[0m)*$')
    match = end_codes.search(old_str)
    end_matches = match.group()
    if len(end_matches) == 4:
        new_end = '\x1b[0m\x1b[0m'
    else:
        new_end = '\x1b[0m'
    twiddle = old_str[:match.span()[0]] + new_end
    return twiddle


def insert_text_block(txt, column, row, txt_width, txt_height):
    """ Input:
            txt: string - a block of text that we want to insert into the
                term.txt file. Lines are separated by newline characters.
            column: int - the offset of the upper lefthand corner of the text
                block (in characters, not pixels or anything). If it's all the
                way to the left, 'column' would be 0. If the text should be
                placed 10 columns from the left, 'column' would be 10.
            row: int - the offset of the upper lefthand corner of the text
                block (in rows from the start of the file). If it's all the way
                at the top of the page, 'row' would be 0.
            txt_width: int - how many characters wide is the text box
            txt_width: int - how many rows does the text box take up
        Output:
            Edits the term.txt file

    It may be that I'll need to rewrite this.
    I think that by doing the reading and writing all in one step I can avoid
    issues with other bits and pieces trying to modify and/or display the
    contents of term.txt, but I could be horrendously wrong.
    """
    txt_lines = [break_line_into_characters(line) for line in txt.split('\n')]
    script_dir = get_script_dir()
    term_file_path = os.path.join(script_dir, 'term.txt')
    with open(term_file_path, 'r+') as f:
        # read old terminal state
        old_data = f.read().split('\n')

        for row_number in range(len(old_data)):
            line = break_line_into_characters(old_data[row_number])
            if row_number < row:
                pass
            elif row_number > (row + txt_height - 1):
                break
            else:
                new_line = line[:column] \
                    + txt_lines[row_number-row] \
                        + line[txt_width+column:]
                old_data[row_number] = ''.join(new_line)

        # write new data to term.txt file
        new_data = '\n'.join(old_data)
        f.seek(0)
        f.write(new_data)
        f.truncate()

if __name__ == "__main__":
    """ Input:
            column: int - how many columns from the left edge of the terminal
                is the text box? A value of 0 will position the text box
                as far left as it will go
            row: int - how many rows from the top of the terminal is the text
                box?
            width: int - how many columns wide is the text box?
            height: int - how many rows tall is the text box?

    Additionally, this script expects text to be fed to it through a Unix pipe.
    example:
        echo 'some text\nnice text' | python update_mirror.py 1 2 9 2

    It will embed the text it receives into term.txt (assuming it is valid).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'column',
        help='How many columns from the left edge of the terminal is this text box?',
        type=int)
    parser.add_argument(
        'row',
        help='How many rows from the top of the terminal is this text box?',
        type=int)
    parser.add_argument(
        'width',
        help='Width of the text box in columns',
        type=int)
    parser.add_argument(
        'height',
        help='Height of the text box in rows',
        type=int)
    args = parser.parse_args()
    text = sys.stdin.read()

    insert_text_block(text, args.column, args.row, args.width, args.height)

    sys.exit(0)
