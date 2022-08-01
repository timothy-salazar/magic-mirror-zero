import os
from update_mirror import get_script_dir

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

if __name__ == "__main__":
    make_term_file()