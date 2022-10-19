"""
Collision testing of shapes.
"""

import gamelib

WIDTH = 400
HEIGHT = 400
DEF_WIDTH = 20
DEF_COLOR = "#333333"
MIN_SIZE = 10
MAX_SIZE = 100

SQUARE = "square"
CIRCLE = "circle"

UNACTIVE_COLOR = "#a4eb34"
ACTIVE_COLOR = "#fa9a14"


def next_shape(shape):
    "Returns the next shape when changing."
    if shape.lower() == SQUARE:
        return CIRCLE
    if shape.lower() == CIRCLE:
        return SQUARE
    return SQUARE # if the shape isn't recognized, use a square


def change_size(current_size, dsize):
    "Changes the size of shape."
    new_size = current_size + dsize
    if new_size < MIN_SIZE or new_size > MAX_SIZE:
        return current_size
    return new_size


def collide_square_with_square(x1, y1, w1, x2, y2, w2):
    "Determines if two squares are colliding."
    return all((x1 + w1 / 2 >= x2 - w2 / 2,
                x1 - w1 / 2 <= x2 + w2 / 2,
                y1 + w1 / 2 >= y2 - w2 / 2,
                y1 - w1 / 2 <= y2 + w2 / 2))


def collide_circle_with_circle(x1, y1, r1, x2, y2, r2):
    "Determines if two circles are colliding."
    dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return dist <= (r1 + r2) / 2


def collide_square_with_circle(sq_x, sq_y, sq_w, cir_x, cir_y, cir_diameter):
    "Determines if a square and a circle are colliding."

    sq_left = sq_x - sq_w / 2
    sq_right = sq_x + sq_w / 2
    sq_top = sq_y - sq_w / 2
    sq_bottom = sq_y + sq_w / 2
    cir_radius = cir_diameter / 2

    edge_x = cir_x
    edge_y = cir_y

    if cir_x < sq_left:
        edge_x = sq_left
    elif cir_x > sq_right:
        edge_x = sq_right
    if cir_y < sq_top:
        edge_y = sq_top
    elif cir_y > sq_bottom:
        edge_y = sq_bottom
    
    dist_x = cir_x - edge_x
    dist_y = cir_y - edge_y
    dist = (dist_x ** 2 + dist_y ** 2) ** 0.5

    return dist <= cir_radius


def draw_bg():
    "Draws the background."
    gamelib.draw_rectangle(0, 0, WIDTH * 1.1, HEIGHT * 1.1, fill='#eeeeee')


def draw_square(x, y, width=DEF_WIDTH, outline='', fill=DEF_COLOR):
    "Draws a square at the given coordinates."
    gamelib.draw_rectangle(x - width / 2,
                           y - width / 2,
                           x + width / 2,
                           y + width / 2,
                           outline=outline,
                           fill=fill)


def draw_circle(x, y, diameter=DEF_WIDTH, outline='', fill=DEF_COLOR):
    "Draws a circle at the given coordinates."
    radius = diameter / 2
    gamelib.draw_oval(x - radius,
                      y - radius,
                      x + radius,
                      y + radius,
                      outline=outline,
                      fill=fill)

def draw_shape(x, y, shape, width, fill):
    "Draws a shape at the cursor coordinates."
    if shape.lower() == SQUARE:
        draw_square(x, y, width=width, fill=fill)
    elif shape.lower() == CIRCLE:
        draw_circle(x, y, diameter=width, fill=fill)


def draw_info():
    "Draws text info on the screen."
    gamelib.draw_text("Press -/+ to decrease/increase cursor shape size\nLeft Click to change cursor shape\nRight click to change objective shape",
                      WIDTH / 2, HEIGHT * 0.15,
                      size=int(WIDTH * 0.03),
                      fill="black")


def main():
    gamelib.title("Collision Test")
    gamelib.resize(WIDTH, HEIGHT)

    cur_x, cur_y = -WIDTH, -HEIGHT # Trash values
    cur_shape = SQUARE
    cur_shape_width = DEF_WIDTH * 2
    cur_color = UNACTIVE_COLOR

    obj_x, obj_y = WIDTH / 2, HEIGHT * 0.6
    obj_shape = SQUARE
    obj_shape_width = int(WIDTH * 0.5)
    obj_color = UNACTIVE_COLOR

    collision = False

    while gamelib.loop():
        cur_color = (UNACTIVE_COLOR if collision else ACTIVE_COLOR)
        obj_color = (ACTIVE_COLOR if collision else UNACTIVE_COLOR)
        gamelib.draw_begin()
        draw_bg()
        draw_shape(obj_x, obj_y, obj_shape, width=obj_shape_width, fill=obj_color)
        draw_shape(cur_x, cur_y, cur_shape, width=cur_shape_width, fill=cur_color)
        draw_info()
        gamelib.draw_end()

        for event in gamelib.get_events():
            if event.type == gamelib.EventType.Motion:
                cur_x, cur_y = event.x, event.y
            elif event.type == gamelib.EventType.ButtonRelease:
                if event.mouse_button == 1:
                    cur_shape = next_shape(cur_shape)
                elif event.mouse_button == 3:
                    obj_shape = next_shape(obj_shape)
            elif event.type == gamelib.EventType.KeyRelease:
                if event.key == 'minus':
                    cur_shape_width = change_size(cur_shape_width, -5)
                elif event.key == 'plus':
                    cur_shape_width = change_size(cur_shape_width, 5)

        if cur_shape == SQUARE and obj_shape == SQUARE:
            collision = collide_square_with_square(cur_x, cur_y, cur_shape_width,
                                                   obj_x, obj_y, obj_shape_width)
        elif cur_shape == CIRCLE and obj_shape == CIRCLE:
            collision = collide_circle_with_circle(cur_x, cur_y, cur_shape_width,
                                                   obj_x, obj_y, obj_shape_width)
        elif cur_shape == SQUARE and obj_shape == CIRCLE:
            collision = collide_square_with_circle(cur_x, cur_y, cur_shape_width,
                                                   obj_x, obj_y, obj_shape_width)
        elif cur_shape == CIRCLE and obj_shape == SQUARE:
            collision = collide_square_with_circle(obj_x, obj_y, obj_shape_width,
                                                   cur_x, cur_y, cur_shape_width)


gamelib.init(main)