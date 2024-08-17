import copy
import random
import sys
import time
import curses
import signal

from datetime import datetime, timedelta


standard_screen = curses.initscr()


SCREEN = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

I = [
    [0, 0, 0, 0],
    [1, 1, 1, 1],
    [0, 0, 0, 0],
]

T = [
    [0, 0, 0],
    [1, 1, 1],
    [0, 1, 0],
]

Z = [
    [1, 1, 0],
    [0, 1, 1],
]

S = [
    [0, 1, 1],
    [1, 1, 0],
]

O = [
    [1, 1],
    [1, 1],
]

J = [
    [1, 1, 1],
    [0, 0, 1],
]

L = [
    [1, 1, 1],
    [1, 0, 0],
]

LINES = 0
SHAPES = [I, T, Z, S, O, J, L]
INITIAL_COORDS = (3, 0)
FALL_EVERY_TIME = timedelta(microseconds=500000)


def rotate_shape(shape):
    return list(map(list, zip(*shape)))[::-1]


def get_new_shape():
    new_shape = copy.deepcopy(SHAPES[random.randint(0, len(SHAPES) - 1)])
    return new_shape


def get_bottom_coords_for_collision(shape):
    x_detected = []
    for y in range(len(shape) - 1, -1, -1):
        for x in range(len(shape[y])):
            if x in x_detected:
                continue
            if shape[y][x] == 1:
                x_detected.append(x)
                yield x, y


def get_left_coords_for_collision(shape):
    for y, cols in enumerate(shape):
        y_found = False
        for x, cell in enumerate(shape[y]):
            if y_found:
                continue
            if cell == 1:
                y_found = True
                yield x, y


def get_right_coords_for_collision(shape):
    for y, cols in enumerate(shape):
        y_found = False
        for x in range(len(shape[y]) - 1, -1, -1):
            cell = shape[y][x]
            if y_found:
                continue
            if cell == 1:
                y_found = True
                yield x, y


def remove_filled_rows(screen):
    global LINES
    global FALL_EVERY_TIME
    removed_lines = 0
    new_screen = []
    for y, row in enumerate(screen):
        if all([col for col in row]):
            removed_lines += 1
            new_screen = [[0] * len(screen[0])] + new_screen
        else:
            new_screen.append(row)
    LINES += removed_lines
    return new_screen, removed_lines


class Keyboard:
    def __init__(self):
        global standard_screen
        self.ss = standard_screen
        self.key = None

    def read_ch(self):
        try:
            self.key = self.ss.getch()
        except curses.error:
            self.key = None

    def is_left_pressed(self) -> bool:
        return self.key == curses.KEY_LEFT

    def is_right_pressed(self) -> bool:
        return self.key == curses.KEY_RIGHT

    def is_down_pressed(self) -> bool:
        return self.key == curses.KEY_DOWN

    def is_action_pressed(self) -> bool:
        return self.key == curses.KEY_UP


def copy_shape_to_screen(shape, shape_x, shape_y, screen):
    for y in range(len(shape)):
        for x in range(len(shape[y])):
            if shape[y][x] == 1:
                screen[y + shape_y][x + shape_x] = 1


def can_continue_shape_fall(shape, shape_x, shape_y, screen) -> bool:
    for bottom_x, bottom_y in get_bottom_coords_for_collision(shape):
        if shape_y + bottom_y == len(screen) - 1 or screen[shape_y + bottom_y + 1][shape_x + bottom_x] == 1:
            return False
    return True



SCREEN_PAIR_COLORS = 1
CURRENT_SHAPE_PAIR_COLORS = 2
NEXT_SHAPE_PAIR_COLORS = 3

SCREEN_COLOR = None
SHAPE_COLOR = None
NEXT_SHAPE_COLOR = None


def draw_virtual_screen(virtual_screen, shape, shape_x, shape_y, next_shape):
    global standard_screen
    global LINES

    rows, cols = standard_screen.getmaxyx()

    width = len(virtual_screen[0]) * 2
    margin_left = (cols // 2) - (width // 2)
    margin_top = 3

    screen_color = [SCREEN_COLOR] if SCREEN_COLOR else []
    shape_color = [SHAPE_COLOR] if SHAPE_COLOR else []
    next_shape_color = [NEXT_SHAPE_COLOR] if NEXT_SHAPE_COLOR else []

    # screen
    last_y = None
    for y, row in enumerate(virtual_screen):
        last_y = y
        standard_screen.addch(y + margin_top, -1 + margin_left, '┃', *screen_color)
        standard_screen.addch(y + margin_top, margin_left + width, '┃', *screen_color)
        for x, cell in enumerate(virtual_screen[y]):
            standard_screen.addstr(y + margin_top, x * 2 + margin_left, '🮘🮘' if cell else '  ', *screen_color)
    standard_screen.addstr(last_y + margin_top + 1, margin_left - 1, '┗' + ('━' * width) + '┛', *screen_color)

    # current shape
    for y, row in enumerate(shape):
        for x, cell in enumerate(shape[y]):
            if cell == 1:
                standard_screen.addstr(y + shape_y + margin_top, (x + shape_x) * 2 + margin_left, '🮘🮘', *shape_color)

    standard_screen.addstr(margin_top, margin_left - 13, f' LINES {LINES}', *screen_color)

    standard_screen.addstr(margin_top, width + margin_left + 5, 'NEXT', *screen_color)
    for y in range(4):
        for x in range(8):
            try:
                cell = next_shape[y][x // 2]
                standard_screen.addch(y + margin_top + 2, width + margin_left + 5 + x, '🮘' if cell else ' ', *next_shape_color)
            except IndexError:
                standard_screen.addch(y + margin_top + 2, width + margin_left + 5 + x, ' ', *next_shape_color)


def show_lines():
    print(f'Lines {LINES}')


def setup_curses():
    global standard_screen
    global SCREEN_COLOR
    global SHAPE_COLOR
    global NEXT_SHAPE_COLOR
    curses.noecho()
    curses.cbreak()
    standard_screen.keypad(True)
    standard_screen.nodelay(True)
    curses.curs_set(0)
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(SCREEN_PAIR_COLORS, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(CURRENT_SHAPE_PAIR_COLORS, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(NEXT_SHAPE_PAIR_COLORS, curses.COLOR_CYAN, curses.COLOR_BLACK)
        SCREEN_COLOR = curses.color_pair(SCREEN_PAIR_COLORS)
        SHAPE_COLOR = curses.color_pair(CURRENT_SHAPE_PAIR_COLORS)
        NEXT_SHAPE_COLOR = curses.color_pair(NEXT_SHAPE_PAIR_COLORS)

def restore_terminal_config():
    global standard_screen
    curses.nocbreak()
    standard_screen.keypad(False)
    curses.echo()
    curses.curs_set(1)
    curses.endwin()


def interrupt_handler(sig, frame):
    restore_terminal_config()
    show_lines()
    sys.exit(0)


def main(screen):
    global LINES
    global FALL_EVERY_TIME

    keyboard = Keyboard()

    setup_curses()
    signal.signal(signal.SIGINT, interrupt_handler)

    shape = get_new_shape()
    next_shape = get_new_shape()
    max_x = len(screen[0]) - 1

    last_fall_movement = datetime.now()

    shape_x, shape_y = INITIAL_COORDS
    while True:
        keyboard.read_ch()

        if keyboard.is_action_pressed():
            rotated_shape = rotate_shape(shape)
            rotated_shape_x, rotated_shape_y = shape_x, shape_y
            for x, y in get_left_coords_for_collision(rotated_shape):
                while rotated_shape_x + x < 0:
                    rotated_shape_x += 1
            for x, y in get_right_coords_for_collision(rotated_shape):
                while rotated_shape_x + x > max_x:
                    rotated_shape_x -= 1
            for y, row in enumerate(rotated_shape):
                for x, cell in enumerate(rotated_shape[y]):
                    if screen[rotated_shape_y + y][rotated_shape_x + x] == 1:
                        break
                else:
                    continue
                break
            else:
                shape = rotated_shape
                shape_x = rotated_shape_x

        if keyboard.is_left_pressed():
            can_move_left = True
            for x, y in get_left_coords_for_collision(shape):
                if shape_x + x == 0:
                    can_move_left = False
                if screen[shape_y + y][shape_x + x - 1] == 1:
                    can_move_left = False
            if can_move_left:
                shape_x -= 1

        elif keyboard.is_right_pressed():
            can_move_right = True
            for x, y in get_right_coords_for_collision(shape):
                if shape_x + x == max_x:
                    can_move_right = False
                elif screen[shape_y + y][shape_x + x + 1] == 1:
                    can_move_right = False
            if can_move_right:
                shape_x += 1

        if keyboard.is_down_pressed() or datetime.now() - last_fall_movement > FALL_EVERY_TIME:
            last_fall_movement = datetime.now()
            if can_continue_shape_fall(shape, shape_x, shape_y, screen):
                shape_y += 1
            else:
                if shape_y == 0:
                    restore_terminal_config()
                    show_lines()
                    sys.exit(0)

                copy_shape_to_screen(shape, shape_x, shape_y, screen)
                shape = next_shape
                next_shape = get_new_shape()
                shape_x, shape_y = INITIAL_COORDS
                screen, removed_lines = remove_filled_rows(screen)
                if removed_lines > 0 and FALL_EVERY_TIME > timedelta(microseconds=80000):
                    FALL_EVERY_TIME = timedelta(microseconds=FALL_EVERY_TIME.microseconds * 0.95)

        virtual_screen = copy.deepcopy(screen)
        draw_virtual_screen(virtual_screen, shape, shape_x, shape_y, next_shape)
        time.sleep(0.01)


if __name__ == '__main__':
    try:
        main(SCREEN)
    except Exception:
        restore_terminal_config()
        raise
