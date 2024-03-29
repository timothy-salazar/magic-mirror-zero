# !/bin/python
# Receives block of text from a plugin and inserts the block of text into the
# term.txt file.
#
import os
import sys
import argparse
import re
from pathlib import Path

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

def get_project_dir():
    """ Returns the path of the project's root directory
    """
    script_dir = get_script_dir()
    path = Path(script_dir).resolve()
    for parent in path.parents:
        stem = parent.stem
        if stem == 'magic-mirror-zero':
            return parent

    raise FileNotFoundError('Could not find project directory')


def break_line_into_characters(line, size=None):
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
    char_list = [i.group(0) for i in get_char.finditer(line)]
    if size and (len(char_list) < size):
        char_list += [' ']*(size - len(char_list))
    return char_list[:size]

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
            txt_width: int - maximum width of the text box (in columns)
            txt_width: int - maximum height of the text box (in rows)
        Output:
            Edits the term.txt file

    It may be that I'll need to rewrite this.
    I think that by doing the reading and writing all in one step I can avoid
    issues with other bits and pieces trying to modify and/or display the
    contents of term.txt, but I could be horrendously wrong.
    """
    # Make the text into a list of lists
    # Truncates list if number of lines exceeds txt_height
    txt_lines = [break_line_into_characters(line, txt_width)
                    for line in txt.split('\n')][:txt_height]
    # Adds lines made of whitespace if number of lines is less than text_height
    if len(txt_lines) < txt_height:
        txt_lines += [[' ']*txt_width]*(txt_height - len(txt_lines))
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
