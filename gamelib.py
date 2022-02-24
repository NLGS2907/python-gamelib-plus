"""
Gamelib+ is an experimental fork of the [gamelib](https://github.com/dessaya/python-gamelib)
library, which is slightly more feature-rich and with type-hinted source code, but maintaining
the simplicity and portability of the original project.

<u>*Any* project built with gamelib should work with gamelib+ too!</u>

https://github.com/NLGS2907/python-gamelib-plus
"""

from os import _exit as os_exit, getcwd
from os.path import abspath, splitext
import signal
from sys import excepthook, exc_info
from threading import Thread, Event as ThreadEvent
from time import time, sleep
import tkinter as tk
from enum import Enum
from logging import INFO, Formatter, Logger, StreamHandler, getLogger
from queue import Empty, Queue
from tkinter import Button, messagebox, simpledialog
from tkinter.font import Font
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


__all__ = ["wait", "get_events", "title", "icon", "draw_begin", "draw_image",
           "draw_text", "draw_arc", "draw_line", "draw_oval", "draw_polygon",
           "draw_rectangle", "draw_button", "draw_end", "resize", "say", "input",
           "is_alive", "loop", "play_sound", "MessageType", "EventType", "Event"]


class MessageType(Enum):
    "An enumeration of the different types of message boxes supported by `say`."

    INFO = 'showinfo'
    "Information message."
    WARNING = 'showwarning'
    "Warning message."
    ERROR = 'showerror'
    "Error message."
    QUESTION = 'askquestion'
    "Question message."
    OKCANCEL = 'askokcancel'
    "Confirmation message."
    YESNO = 'askyesno'
    "Yes or No question message."
    YESNOCANCEL = 'askyesnocancel'
    "Yes or No question with cancel option message."
    RETRY = 'askretrycancel'
    "Retry message."


class InvalidMessageType(Exception):
    "The user used an incorrect type of message."

    def __init__(self) -> None:

        super().__init__(f"Invalid type message type. The valid types are: {', '.join([msgtype.name.lower() for msgtype in MessageType])}")


class EventType(Enum):
    "An enumeration of the different types of `Event`s supported by gamelib."

    KeyPress = 'KeyPress'
    "The user pressed a key."
    KeyRelease = 'KeyRelease'
    "The user released a key."
    Motion = 'Motion'
    "The user moved the mouse over the window."
    ButtonPress = 'ButtonPress'
    "The user pressed a mouse button."
    ButtonRelease = 'ButtonRelease'
    "The user released a mouse button."


class Event:
    """
    Represents an event generated by the user.

    Attributes:
        type: An `EventType`.
        key: A key that has been pressed/released.
        mouse_button: 1, 2 or 3 for left, right and middle mouse buttons respectively.
                      Also supports 4 and 5 for when the mouse wheel is scrolled up or down.
        x: The current mouse horizontal position, in pixels.
        y: The current mouse vertical position, in pixels.

    This is actually a wrapper for the
    [Tkinter Event class](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-handlers.html).
    Any of the `tk.Event` attributes can be accessed through this object.

    ## See also

    `wait`, `get_events`
    """

    def __init__(self, tkevent: tk.Event) -> None:

        self.tkevent = tkevent

    def __getattr__(self, k: str) -> Any:
        "Gets an attribute from `Event`."

        if k == "type":
            return EventType[self.tkevent.type.name]
        if k == "key":
            return self.tkevent.keysym
        if k == "mouse_button":
            return self.tkevent.num
        if k == "x":
            return self.tkevent.x
        if k == "y":
            return self.tkevent.y
        return getattr(self.tkevent, k)


    def __repr__(self) -> str:
        "Represents the event in the form of a string."

        return repr(self.tkevent)


class _TkLogger:
    "Logger for debug and information purposes."

    def __new__(cls) -> "_TkLogger":
        """
        Returns the instance of the class, which is unique
        and there can't be duplicates.
        """

        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self,
                 *,
                 log_name: str="gamelib_log",
                 log_level: int=INFO,
                 fmt: str="[%(levelname)s] %(message)s",
                 date_fmt: str="%d-%m-%Y %I:%M:%S %p") -> None:
        "Initializes `_TkLogger`."

        super().__init__()

        self.formatter: Formatter = Formatter(fmt=fmt, datefmt=date_fmt)
        self.handler: StreamHandler = StreamHandler()
        self.handler.setFormatter(self.formatter)

        self.logger: Logger = getLogger(log_name)
        self.logger.setLevel(log_level)
        self.logger.addHandler(self.handler)


    def debug(self, message: str, *args, **kwargs) -> None:
        "Registers an event of level DEBUG."

        self.logger.debug(message, *args, **kwargs)


    def info(self, message: str, *args, **kwargs) -> None:
        "Registers an event of level INFO."

        self.logger.info(message, *args, **kwargs)


    def warning(self, message: str, *args, **kwargs) -> None:
        "Registers an event of level WARNING."

        self.logger.warning(message, *args, **kwargs)


    def error(self, message: str, *args, **kwargs) -> None:
        "Registers an event of level ERROR."

        self.logger.error(message, *args, **kwargs)


    def critical(self, message: str, *args, **kwargs) -> None:
        "Registers an event of level CRITICAL."

        self.logger.critical(message, *args, **kwargs)


log = _TkLogger()


class _TkWindow(tk.Tk):
    "The window that will be used."

    instance: "_TkWindow" = None
    initialized: ThreadEvent = ThreadEvent()
    commands: Queue = Queue()

    busy_count: int = 0
    idle: ThreadEvent = ThreadEvent()
    idle.set()


    def __init__(self) -> None:
        "Initializes `_TkWinddow`"

        super().__init__()

        self.closed: bool = False

        self.title("Gamelib+")
        self.resizable(False, False)

        self.assets: Dict[str, Union[Font, tk.PhotoImage]] = {}
        self.buttons: Dict[Tuple[int, int], Button] = {}

        self.canvas: tk.Canvas = tk.Canvas(background="black")
        self.canvas.grid(column=0, row=0, sticky="nwes")

        for event_type in EventType:
            self.bind(f"<{event_type.name}>", self.handle_event)
        self.bind(f"<<notify>>", self.process_commands)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.canvas.focus_set()
        self.after_idle(self.process_commands)


    def close(self) -> None:
        "Ultimately closes window."

        self.closed = True
        self.quit()
        self.update()


    def notify(self) -> None:
        "Generates a <notify> event."

        if not self.closed:
            self.event_generate("<<notify>>", when="tail")


    def process_commands(self, *args) -> None:
        "Processes all commands in `_TkWindow.commands`."

        _TkWindow.busy_count += 1
        _TkWindow.idle.clear()
        try:
            while True:
                try:
                    method, *args = _TkWindow.commands.get(False)
                    getattr(self, method)(*args)
                except Empty:
                    break
        finally:
            _TkWindow.busy_count -= 1
            if _TkWindow.busy_count == 0:
                _TkWindow.idle.set()


    def handle_event(self, tkevent: tk.Event) -> None:
        "Puts an event in the queue so it can be processed."

        if any(isinstance(tkevent.widget, class_check) for class_check in [Button]):
            tkevent.x = tkevent.x_root - self.canvas.winfo_rootx()
            tkevent.y = tkevent.y_root - self.canvas.winfo_rooty()

        _GameThread.events.put(Event(tkevent))


    def resize(self, w: int, h: int) -> None:
        "Resizes the canvas, and in this case, also the window."

        self.canvas.configure(width=w, height=h)


    def clear(self, full: bool=False) -> None:
        """
        Clears all elements in the canvas except the sub-windows.
        Set `full` to `True` for this.
        """

        for tag in ("text", "figure", "image") + (("window") if full else ()):
            self.canvas.delete(tag)


    def icon(self, path: str) -> None:
        "Changes the icon of the main window."

        self.tk.call("wm", "iconphoto", self._w, self.get_image(path))


    def draw_image(self, path: str, x: int, y: int, anchor: str="nw") -> None:
        "Draws an image in the canvas."

        self.canvas.create_image(x, y, anchor=anchor, image=self.get_image(path), tag="image")


    def draw(self, type: str, args, kwargs) -> None:
        "Draws a figure in the canvas."

        options = {"fill": "white", "tag": "figure"}
        options.update(kwargs)
        getattr(self.canvas, f"create_{type}")(*args, **options)


    def draw_button(self, x: int, y: int, options) -> None:
        "Draws a button in the canvas."

        if "image" in options:
            options["image"] = self.get_image(options["image"])

        button = Button(master=self, **options)
        if (x, y) not in self.buttons and button["text"] not in (btn["text"] for btn in self.buttons.values()):
            self.buttons[(x, y)] = button
            self.canvas.create_window(x, y, tags="window", window=button, anchor='c')


    def draw_text(self, text: str, x: int, y: int, font: str, size: int, bold: True, italic: True, kwargs) -> None:
        "Draws text lines in the canvas."

        options = {"fill": "white"}
        options.update(kwargs)
        self.canvas.create_text(x, y, text=text, font=self.get_font(font, size, bold, italic), tag="text", **options)


    def get_font(self, family: str, size: int, bold: True, italic: True) -> Font:
        "Generates and saves the font to be used."

        weight = "normal"
        if bold:
            weight = "bold"
        slant = "roman"
        if italic:
            slant = "italic"
        name = f"font-{family}-{size}-{weight}-{slant}"
        if name not in self.assets:
            self.assets[name] = Font(family=family, size=size, weight=weight, slant=slant)
        return self.assets[name]


    def get_image(self, path: str) -> tk.PhotoImage:
        "Generates and saves the image to be used."

        if path not in self.assets:
            check_image_format(path)
            self.assets[path] = tk.PhotoImage(file=path)
        return self.assets[path]


    def say(self, message: str, msg_type: str, done: Queue) -> None:
        "Prompts a message box of a given type in the canvas."

        if isinstance(msg_type, MessageType):
            message_type = msg_type.value
        elif isinstance(msg_type, str) and msg_type.upper() in (msgtype.name for msgtype in MessageType):
            message_type = getattr(MessageType, msg_type.upper()).value
        else:
            raise InvalidMessageType()
        response = getattr(messagebox, message_type)(self.title(), message, parent=self)
        done.put(response)


    def input(self, prompt: str, response: Queue) -> None:
        "Prompts a box able to take user input."

        response.put(simpledialog.askstring(self.title(), prompt, parent=self))


def check_image_format(path: str) -> None:
    "Produce a warning message if the image format is not supported"

    ext = splitext(path)[1].lower()
    supported = (".gif", ".ppm", ".pgm", ".pbm")
    if ext not in supported:
        log.warning(f"{path}: image format {ext} is not supported and may not work properly on some platforms (Windows/Mac/Linux).\n" +
                    f"Please use one of: {supported}.")


def check_audio_format(path: str) -> None:
    "Produce a warning message if the audio format is not supported"

    ext = splitext(path)[1].lower()
    if ext != ".wav":
        log.warning(f"{path}: audio format {ext} is not supported and may not work properly on some platforms (Windows/Mac/Linux).\n" +
                    f"Please use WAV.")


def _audio_init() -> Callable[[str], None]:
    # shamelessly stolen from https://github.com/TaylorSMarks/playsound

    class PlaysoundException(Exception):
        "Custom Exception for sound validation."

        ...


    def _playsoundWin(sound: str) -> None:
        "Plays a sound for Windows."

        from ctypes import c_buffer, windll
        from random import random
        from sys import getfilesystemencoding

        def winCommand(*command: Tuple[str, ...]):
            "Executes a Windows Command."

            buf = c_buffer(255)
            command = ' '.join(command).encode(getfilesystemencoding())
            errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
            if errorCode:
                errorBuffer = c_buffer(255)
                windll.winmm.mciGetErrorStringA(errorCode, errorBuffer, 254)
                exceptionMessage = ("\n    Error " + str(errorCode) + " for command:"
                                    "\n        " + command.decode() +
                                    "\n    " + errorBuffer.value.decode(getfilesystemencoding(), "ignore"))
                raise PlaysoundException(exceptionMessage)
            return buf.value

        alias = "playsound_" + str(random())
        winCommand("open \"" + sound + "\" alias", alias)
        winCommand("set", alias, "time format milliseconds")
        durationInMS = winCommand("status", alias, "length")
        winCommand("play", alias, "from 0 to", durationInMS.decode())


    def _playsoundOSX(sound: str) -> None:
        "Plays a soundd for Mac"

        from AppKit import NSSound
        from Foundation import NSURL

        if "://" not in sound:
            if not sound.startswith('/'):
                sound = getcwd() + '/' + sound
            sound = "file://" + sound
        url   = NSURL.URLWithString_(sound)
        nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
        if not nssound:
            raise IOError("Unable to load sound named: " + sound)
        nssound.play()


    def _playsoundNix(sound: str) -> None:
        "Plays a sound for Unix (Linux)."

        from urllib.request import pathname2url

        import gi
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst

        Gst.init(None)

        playbin = Gst.ElementFactory.make("playbin", "playbin")
        if sound.startswith(("http://", "https://")):
            playbin.props.uri = sound
        else:
            playbin.props.uri = "file://" + pathname2url(abspath(sound))

        set_result = playbin.set_state(Gst.State.PLAYING)
        if set_result != Gst.StateChangeReturn.ASYNC:
            raise PlaysoundException(
                "playbin.set_state returned " + repr(set_result))

        bus = playbin.get_bus()
        bus.add_signal_watch()
        def on_message(bus, message):
            if message.type in (Gst.MessageType.EOS, Gst.MessageType.ERROR):
                playbin.set_state(Gst.State.NULL)
        bus.connect("message", on_message)

    from platform import system
    system = system()


    def play_sound(sound: str) -> None:
        """
        Play a sound located at the given path.

        Example:
            ```
            gamelib.play_sound('sound/jump.wav')
            ```

        Note:
            The only sound format that is supported accross all platforms (Windows/Mac/Linux)
            is WAV.
        """

        check_audio_format(sound)
        if system == 'Windows':
            _playsoundWin(sound)
        elif system == 'Darwin':
            _playsoundOSX(sound)
        else:
            _playsoundNix(sound)

    return play_sound


class _GameThread(Thread):
    "The game thread to be used."

    _instance: "_GameThread"
    initialized: ThreadEvent
    events: Queue


    def __new__(cls) -> "_GameThread":
        "Returns the unique instance of `_GameThread`"

        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
            cls.initialized= ThreadEvent()
            cls.events = Queue()
        return cls._instance


    def start(self, game_main: Callable[..., None], args) -> None:
        "Starts and sets up the thread."

        self.game_main = game_main
        self.args = args
        super().start()


    def run(self) -> None:
        "Runs the thread."

        try:
            self.game_main(*self.args)
        except Exception as e:
            excepthook(*exc_info())
        finally:
            self.send_command_to_tk('close', notify=True)


    def notify_tk(self) -> None:
        """
        Waits for `_TkWindow` and notifies it so it
        generates the <notify> event.
        """

        self.wait_for_tk()
        w = _TkWindow.instance
        if w:
            w.notify()


    def wait_for_tk(self) -> None:
        """
        Initializes the thread and waits until the window
        also is initialized.
        """

        if not _TkWindow.initialized.is_set():
            _GameThread.initialized.set()

            # block until Tk is initialized
            _TkWindow.initialized.wait()


    def send_command_to_tk(self, *args, notify: bool=False) -> None:
        "Enqueues a command to be processed later."

        _TkWindow.commands.put(args)
        if notify:
            self.notify_tk()


    def wait(self, event_types: Union[EventType, Tuple[EventType, ...], None]=None) -> Optional[Event]:
        """
        Wait until the next `Event`: a key is pressed/released, the mouse is moved, etc,
        and return it.

        This function is normally used in combination with `gamelib.is_alive`,
        in turn-based games.

        Args:
            event_type: If an `EventType` is passed, the function will ignore any
                        events that are not of this type. (It will still return `None`
                        when the game is closed).
                        It also accepts a tuple of event types, so it can listen to
                        more than one type.

        Returns:
            An `Event`, or `None` if the user closed the game window.

        Example:
            ```
            while gamelib.is_alive():
                event = gamelib.wait(gamelib.EventType.KeyPress):
                gamelib.say(f'You pressed {event.key}')
            ```
        """

        self.notify_tk()
        if not _TkWindow.instance:
            return None
        while True:
            event = _GameThread.events.get()
            if any((not event, not event_types,
                   (isinstance(event_types, EventType) and event.type == event_types),
                   (isinstance(event_types, Tuple) and event.type in event_types))):
                return event


    def get_events(self) -> List[Event]:
        """
        Get the list of `Event`s that happened since the last call to `get_events`.

        This function is normally used in combination with `loop`, in action games.

        Example:
            ```
            while gamelib.loop(fps=30):
                # this is executed 30 times per second
                for event in gamelib.get_events():
                    if event.type == gamelib.EventType.KeyPress and event.key == 'q':
                        return
            ```
        """
    
        self.notify_tk()
        events = []
        while True:
            try:
                event = _GameThread.events.get(False)
                if not event:
                    break
                events.append(event)
            except Empty:
                break
        return events


    def title(self, s: str) -> None:
        "Set the window title to `s`."

        self.send_command_to_tk('title', s)


    def icon(self, path: str) -> None:
        """
        Set the window icon to the image located at `path`.

        Example:
            ```
            gamelib.icon('images/icon.gif')
            ```

        Note:
            The only image formats that are supported accross all platforms (Windows/Mac/Linux)
            are GIF and PPM/PGM/PBM.
        """

        self.send_command_to_tk('icon', path)


    def draw_begin(self) -> None:
        """
        Clear the window.

        Any call to `draw_*` should be between `draw_begin` and `draw_end`.

        Example:
            ```
            gamelib.draw_begin()
            gamelib.draw_rectangle(0, 0, 10, 10, fill='red')
            gamelib.draw_end()
            ```
        """

        _TkWindow.idle.wait()
        self.send_command_to_tk('clear')


    def draw_image(self, path: str, x: int, y: int) -> None:
        """
        Draw an image located at `path` in the coordinates `x, y`.

        Example:
            ```
            gamelib.draw_image('images/player.gif', 10, 10)
            ```

        Note:
            The only image formats that are supported accross all platforms (Windows/Mac/Linux)
            are GIF and PPM/PGM/PBM.
        """

        self.send_command_to_tk('draw_image', path, x, y)


    def draw_text(self, text: str, x: int, y: int, font: Optional[str]=None, size: int=12, bold: bool=False, italic: bool=False, **options) -> None:
        """
        Draw some `text` at coordinates `x, y` with the given properties.

        Args:
            text: The text to draw.
            x:    The screen coordinates for the text.
            y:    The screen coordinates for the text.
            font: Font family name (eg: `'Helvetica'`). **Note:** the only font guaranteed to be
                  available in all systems is the default font. If the selected font is not found,
                  the default font will be used instead.
            size: Size of the text.
            bold: Whether or not to use bold weight.
            italic: Whether or not to use italic slant.

        Some of the supported extra options are:

        * `fill`: Fill color. It can be named colors like `'red'`, `'white'`, etc,
          or a specific color in `'#rrggbb'` hexadecimal format.
        * `anchor`: Where to place the text relative to the given position.
          It may be any combination of `n` (North), `s` (South), `e`
          (East), `w` (West) and `c` (center). Default is `c`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_text`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_text.html).

        Example:
            ```
            gamelib.draw_text('Hello world!', 10, 10, fill='red', anchor='nw')
            ```
        """

        self.send_command_to_tk('draw_text', text, x, y, font, size, bold, italic, options)


    def draw_arc(self, x1: int, y1: int, x2: int, y2: int, **options) -> None:
        """
        Draw an arc, pieslice, or chord in the bounding box between points `x1, y1` and
        `x2, y2`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_arc`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_arc.html).

        Example:
            ```
            gamelib.draw_arc(10, 10, 20, 20, outline='white', fill='red')
            ```
        """

        self.send_command_to_tk('draw', 'arc', [x1, y1, x2, y2], options)


    def draw_line(self, x1: int, y1: int, x2: int, y2: int, **options) -> None:
        """
        Draw a straight line between points `x1, y1` and `x2, y2`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_line`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_line.html).

        Example:
            ```
            gamelib.draw_line(10, 10, 30, 20, fill='blue', width=2)
            ```
        """

        self.send_command_to_tk('draw', 'line', [x1, y1, x2, y2], options)


    def draw_oval(self, x1: int, y1: int, x2: int, y2: int, **options) -> None:
        """
        Draw an ellipse in the bounding box between points `x1, y1` and `x2, y2`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_oval`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_oval.html).

        Example:
            ```
            gamelib.draw_oval(10, 10, 30, 20, outline='white', fill='red')
            ```
        """

        self.send_command_to_tk('draw', 'oval', [x1, y1, x2, y2], options)


    def draw_polygon(self, points: List[int], **options) -> None:
        """
        Draw a polygon with vertices in the given `points` coordinates list. The list must have
        an even amount of numbers; each pair determines a vertex. The last vertex is automatically
        joined with the first one with a segment.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_polygon`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_polygon.html).

        Example:
            ```
            gamelib.draw_polygon([10, 10, 30, 20, 0, 40], outline='white', fill='red')
            ```
        """

        self.send_command_to_tk('draw', 'polygon', points, options)


    def draw_rectangle(self, x1: int, y1: int, x2: int, y2: int, **options) -> None:
        """
        Draw an rectangle in the bounding box between points `x1, y1` and `x2, y2`.

        To see all supported options, see the documentation for
        [`tkinter.Canvas.create_rectangle`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/create_rectangle.html).

        Example:
            ```
            gamelib.draw_rectangle(10, 10, 30, 20, outline='white', fill='red')
            ```
        """

        self.send_command_to_tk('draw', 'rectangle', [x1, y1, x2, y2], options)


    def draw_button(self, x: int, y: int, **options) -> None:
        """
        Draws a button at the coordinates `x, y`.

        Some of the supported options are:

        * `text`: The text to display on this button.
        * `background` or `bg`: Button Background fill color.
        * `foreground` or `fg`: Button Text fill color.
        * `command`: The handler function to be used as a callback for this button.

        To see all supported options, see the documentation for
        [`tkinter.Button`](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/button.html)

        Example:
            ```
            gamelib.draw_button(20, 20, text='say hello', background='black', foreground='white', command=(lambda : print('hello!')))
            ```
        """

        self.send_command_to_tk('draw_button', x, y, options)


    def draw_end(self) -> None:
        """
        Refresh the window.

        Any call to `draw_*` should be between `draw_begin` and `draw_end`.

        Example:
            ```
            gamelib.draw_begin()
            gamelib.draw_rectangle(0, 0, 10, 10, fill='red')
            gamelib.draw_end()
            ```
        """

        self.send_command_to_tk('update', notify=True)


    def resize(self, width: int, height: int) -> None:
        "Resize the window to be `width` pixels wide and `height` pixels tall."

        self.send_command_to_tk('resize', width, height)


    def say(self, message: str, msg_type: str='info') -> Optional[bool]:
        """
        Present the user with the given `message` in a dialog box, depending on the type.
        Available types are `info`, `warning`, `error`, `question`, `okcancel`, `yesno`,
        `yesnocancel` or `retry`.
        The default is `info`.
        """

        done = Queue()
        self.send_command_to_tk('say', message, msg_type, done, notify=True)
        return done.get()


    def input(self, prompt: str) -> Optional[str]:
        """
        Ask the user to enter a text value.

        Args:
            prompt: A message to display.

        Returns:
            A string containing the value that the user typed. `None` if the user
            clicked on Cancel instead of OK.
        """

        response = Queue()
        self.send_command_to_tk('input', prompt, response, notify=True)
        return response.get()


    def is_alive(self) -> bool:
        """
        Returns `True` if the game window is open, or `False` otherwise.

        Example:
            ```
            while gamelib.is_alive():
                event = gamelib.wait(gamelib.EventType.KeyPress):
                gamelib.say(f'You pressed {event.key}')
            ```
        """

        self.wait_for_tk()
        return bool(_TkWindow.instance)

    _last_loop_time = None


    def loop(self, fps: int=30) -> bool:
        """
        When used in a `while` loop, the body will be executed `fps` times per second.

        Returns:
            `True` if the game window is still open, `False` otherwise.

        Example:
            ```
            while gamelib.loop(fps=30):
                # this is executed 30 times per second
                for event in gamelib.get_events():
                    if event.type == gamelib.EventType.KeyPress and event.key == 'q':
                        return
            ```
        """

        frame_duration = 1.0 / fps
        a = _GameThread._last_loop_time
        b = time()
        if a:
            sleep(max(0, frame_duration - (b - a)))
        _GameThread._last_loop_time = time()
        return self.is_alive()


# Module Aliases
wait = _GameThread().wait
get_events = _GameThread().get_events
title = _GameThread().title
icon = _GameThread().icon
draw_begin = _GameThread().draw_begin
draw_image = _GameThread().draw_image
draw_text = _GameThread().draw_text
draw_arc = _GameThread().draw_arc
draw_line = _GameThread().draw_line
draw_oval = _GameThread().draw_oval
draw_polygon = _GameThread().draw_polygon
draw_rectangle = _GameThread().draw_rectangle
draw_button = _GameThread().draw_button
draw_end = _GameThread().draw_end
resize = _GameThread().resize
say = _GameThread().say
input = _GameThread().input
is_alive = _GameThread().is_alive
loop = _GameThread().loop
play_sound = _audio_init()


def _sigint_handler(sig, frame) -> None:
    w = _TkWindow.instance
    if w:
        w.close()
    else:
        raise KeyboardInterrupt()


def init(game_main: Callable[..., None], args=None) -> None:
    """
    Initialize gamelib.

    Args:
        game_main: Your `main` function.
        args: List of arguments to be passed to the `main` function, or `None`.
    """

    _GameThread().start(game_main, args or [])

    # block until wait(), get_events(), etc called on game thread.
    # This prevents rendering the window before the user has a chance to configure it.
    _GameThread.initialized.wait()

    _TkWindow.instance = _TkWindow()
    _TkWindow.initialized.set()

    signal.signal(signal.SIGINT, _sigint_handler)

    try:
        _TkWindow.instance.mainloop()
    finally:
        _GameThread.events.put(None)
        _TkWindow.instance = None
        _GameThread._instance.join(1)
        if _GameThread().is_alive():
            log.info('Killing unresponsive game thread. Make sure to call get_events() or wait() periodically.')
            os_exit(1)
        os_exit(0)


if __name__ == '__main__':
    def interactive_main(_locals):
        "Emulates an interactive interface of Python interpreter."
        import code
        code.interact(local=_locals)

    init(interactive_main, args=[locals()])
