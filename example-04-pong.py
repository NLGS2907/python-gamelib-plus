"""
The game Pong!
Keys:
    Left player:  Q/A
    Right player: Up/Down arrow keys
"""

import gamelib
from collections import namedtuple
import random

SIZE = 300, 300

PADDLE1 = 0
PADDLE2 = 1

PADDLE_GAP = 10
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 60

BALL_RADIUS = 5

FPS = 30
VELOCITY = 150 / FPS

State = namedtuple('State', ['paddles', 'ball_pos', 'ball_vel', 'score'])


def move_paddle(state, paddle, dy):
    "Handles vertical paddle movement."
    W, H = SIZE
    paddles = list(state.paddles)
    y1, y2 = paddles[paddle]
    y1 += dy * VELOCITY * 1.5
    y2 += dy * VELOCITY * 1.5
    if y1 < 0 or y2 > H:
        return state
    paddles[paddle] = (y1, y2)
    return state._replace(paddles=tuple(paddles))


def paddle_collision(state, paddle):
    "Handles the ball-paddle collision."
    W, H = SIZE
    bx, by = state.ball_pos

    py1, py2 = state.paddles[paddle]
    py_mid = (py1 + py2) / 2
    px = PADDLE_GAP if paddle == PADDLE1 else H - PADDLE_GAP

    return not ((abs(bx - px) > PADDLE_WIDTH / 2 + BALL_RADIUS)
                or (abs(by - py_mid) > PADDLE_HEIGHT / 2 + BALL_RADIUS))


def move_ball(state):
    "Moves the ball itself."
    W, H = SIZE
    x, y = state.ball_pos
    vx, vy = state.ball_vel

    x = x + vx * VELOCITY
    y = y + vy * VELOCITY

    if y < BALL_RADIUS or y > H - BALL_RADIUS:
        vy = -vy

    if (
        (vx < 0 and paddle_collision(state, PADDLE1)) or
        (vx > 0 and paddle_collision(state, PADDLE2))
    ):
        vx = -vx
        vy += 2 * (random.random() - 0.5)

    return state._replace(ball_pos=(x, y), ball_vel=(vx, vy))


def draw_paddle(state, paddle):
    "Draws one paddle element."
    W, H = SIZE
    x = PADDLE_GAP if paddle == 0 else H - PADDLE_GAP
    y1, y2 = state.paddles[paddle]
    gamelib.draw_rectangle(
        x - PADDLE_WIDTH / 2,
        y1,
        x + PADDLE_WIDTH / 2,
        y2,
        fill='white',
    )


def draw_ball(state):
    "Draws the ball itself."
    x, y = state.ball_pos
    gamelib.draw_oval(
        x - BALL_RADIUS,
        y - BALL_RADIUS,
        x + BALL_RADIUS,
        y + BALL_RADIUS,
        fill='white',
    )


def random_ball_velocity():
    "Generate a random velocity for the ball to take."
    vx, vy = 1 if random.random() > 0.5 else -1, random.random()
    norm = (vx * vx + vy * vy) ** 0.5
    return vx / norm, vy / norm


def check_goal(state):
    "Checks collision againts the boundaires behind the paddles."
    W, H = SIZE
    x, y = state.ball_pos
    vx, vy = state.ball_vel
    score1, score2 = state.score

    if vx > 0 and x > W:
        return state._replace(
            ball_pos=(W / 2, H / 2),
            ball_vel=random_ball_velocity(),
            score=(score1 + 1, score2),
        )
    if vx < 0 and x < 0:
        return state._replace(
            ball_pos=(W / 2, H / 2),
            ball_vel=random_ball_velocity(),
            score=(score1, score2 + 1),
        )
    return state


def draw_score(state):
    "Updates the score."
    W, H = SIZE
    score1, score2 = state.score
    gamelib.draw_text(f"{score1} - {score2}", W / 2, 10, anchor='n', fill='white')


def main():
    gamelib.title("Pong")

    W, H = SIZE
    MID_H = H / 2
    gamelib.resize(W, H)

    state = State(
        paddles=((MID_H - PADDLE_HEIGHT / 2, MID_H + PADDLE_HEIGHT / 2),
                 (MID_H - PADDLE_HEIGHT / 2, MID_H + PADDLE_HEIGHT / 2)),
        ball_pos=(W / 2, H / 2),
        ball_vel=random_ball_velocity(),
        score=(0, 0),
    )

    while gamelib.loop():
        gamelib.draw_begin()
        draw_paddle(state, PADDLE1)
        draw_paddle(state, PADDLE2)
        draw_ball(state)
        draw_score(state)
        gamelib.draw_end()

        if gamelib.key_pressed('q'):    state = move_paddle(state, PADDLE1, -1)
        if gamelib.key_pressed('a'):    state = move_paddle(state, PADDLE1, +1)
        if gamelib.key_pressed('Up'):   state = move_paddle(state, PADDLE2, -1)
        if gamelib.key_pressed('Down'): state = move_paddle(state, PADDLE2, +1)

        state = move_ball(state)
        state = check_goal(state)

gamelib.init(main)
