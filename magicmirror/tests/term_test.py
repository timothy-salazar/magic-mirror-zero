""" Some general tests to see if everything is working with the terminal.
"""
import os
import random

def get_random_block():
    """This is using some ANSI escape sequences to make a block with a random
    color over a background of another random color.
    A character occupies a rectangle twice as tall as it is wide. The character
    we're using here is \u2580, which corresponds to a solid block taking up
    the top half of that rectangle
    """
    base = '\033[38;2;{};{};{};48;2;{};{};{}m\u2580\033[0m'
    block = base.format(*(random.randrange(0, 255) for i in range(6)))
    return block

def get_solid_block():
    """This is using some ANSI escape sequences to make a block with a random
    color over a background of another random color.
    A character occupies a rectangle twice as tall as it is wide. The character
    we're using here is \u2580, which corresponds to a solid block taking up
    the top half of that rectangle
    """
    base = '\033[38;2;{0};{1};{2};48;2;{0};{1};{2}m\u2580\033[0m'
    block = base.format(*(random.randrange(0, 255) for i in range(3)))
    return block

def fill_screen_random(width, height):
    """ Fills the screen with randomly colored blocks
    """
    screen_text = ''
    for y in range(height):
        for x in range(width):
            screen_text += get_random_block()
        screen_text += '\n'
    # we use strip() here to get rid of the last new line character
    return screen_text.strip()

def fill_screen_solid(width, height):
    """ Fills the screen with randomly colored blocks
    """
    screen_text = ''
    block = get_solid_block()
    for y in range(height):
        for x in range(width):
            screen_text += block
        screen_text += '\n'
    # we use strip() here to get rid of the last new line character
    return screen_text.strip()

def main():
    """gets the width and height of the terminal in columns and lines, then
    fills it with randomly colored blocks. 
    This is mainly just to see that everything is working as expected.
    """
    width, height = os.get_terminal_size()
    print(f'Width: {width} Height: {height}')
    print(fill_screen_random(width, height))

if __name__ == "__main__":
    main()