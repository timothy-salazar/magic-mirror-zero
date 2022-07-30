""" Receives block of text from a plugin and inserts the block of text into the
term.txt file.
"""
import os
import sys
import argparse

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
    txt_lines = txt.split('\n')
    script_dir = get_script_dir()
    term_file_path = os.path.join(script_dir, 'term.txt')
    with open(term_file_path, 'r+') as f:
        old_data = f.read().split('\n')
        for row_number in range(len(old_data)):
            line = old_data[row_number]
            if row_number < row:
                pass
            elif row_number > (row + txt_height - 1):
                break
            else:
                new_line = line[:column] \
                    + txt_lines[row_number-row] \
                        + line[txt_width+column:]
                old_data[row_number] = new_line
        new_data = '\n'.join(old_data)
        f.seek(0)
        f.write(new_data)

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
