"""
This example shows a rectangle moving around the window.
"""

import random

import gamelib

WIDTH = 300
HEIGHT = 300
MARGIN = 5
SQ_WIDTH = 20


def _get_random_color():
    "Generates a random HEX color."
    return f"#{''.join(random.choice('0123456789abcdef') for _ in range(6))}"


def main():
    gamelib.resize(WIDTH, HEIGHT)

    sq_x, sq_y = 150, 80
    sq_color = _get_random_color()
    x1, y1, x2, y2 = ((sq_x - SQ_WIDTH / 2), (sq_y - SQ_WIDTH / 2),
                      (sq_x + SQ_WIDTH / 2), (sq_y + SQ_WIDTH / 2))
    dx, dy = 5.0, 5.0

    while gamelib.loop():
        for event in gamelib.get_events():
            if event.type == gamelib.EventType.KeyPress and event.key == 'q':
                return

        gamelib.draw_begin()
        gamelib.draw_rectangle(x1, y1, x2, y2, fill=sq_color)
        gamelib.draw_end()

        x1 += dx
        y1 += dy
        x2 += dx
        y2 += dy
        if x2 > WIDTH - MARGIN or x1 < MARGIN:
            dx *= -1
            sq_color = _get_random_color()
        if y2 > HEIGHT - MARGIN or y1 < MARGIN:
            dy *= -1
            sq_color = _get_random_color()

gamelib.init(main)
