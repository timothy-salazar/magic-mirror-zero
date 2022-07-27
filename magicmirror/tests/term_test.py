""" Some general tests to see if everything is working with the terminal.
"""
import os
import random

def get_random_block():
    base = '\033[38;2;{};{};{};48;2;{};{};{}m\u2580\033[0m'
    block = base.format(*(random.randrange(0,255) for i in range(6)))
    return block

def fill_screen(width, height):
    s = ''
    for y in range(height):
        for x in range(width):
            s += get_random_block()
        s += '\n'
    print(s.strip())

def main():
    width, height = os.get_terminal_size()
    print(f'Width: {width} Height: {height}')
    fill_screen(width, height)

if __name__ == "__main__":
    main()