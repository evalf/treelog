import sys
import typing

from ._context import ContextLog
from .proto import Level


class RichOutputLog(ContextLog):
    '''Output rich (colored,unicode) text to stream.'''

    _cmap = (
        '\033[1;30m',  # debug: bold gray
        '\033[1m',  # info: bold
        '\033[1;34m',  # user: bold blue
        '\033[1;35m',  # warning: bold purple
        '\033[1;31m')  # error: bold red

    def __init__(self) -> None:
        super().__init__()
        self._current = ''  # currently printed context
        set_ansi_console()

    def contextchangedhook(self) -> None:
        _current = ''.join(item + ' > ' for item in self.currentcontext)
        if _current == self._current:
            return
        n = first(c1 != c2 for c1, c2 in zip(_current, self._current))
        items = []
        if n == 0 and self._current:
            items.append('\r')
        elif n < len(self._current):
            items.append('\033[{}D'.format(len(self._current)-n))
        if n < len(_current):
            items.append(_current[n:])
        if len(_current) < len(self._current):
            items.append('\033[K')
        sys.stdout.write(''.join(items))
        sys.stdout.flush()
        self._current = _current

    def write(self, msg, level: Level) -> None:
        sys.stdout.write(
            ''.join([self._cmap[level.value], str(msg), '\033[0m\n', self._current]))


def first(items: typing.Iterable[bool]) -> int:
    'return index of first truthy item, or len(items) of all items are falsy'
    i = 0
    for item in items:
        if item:
            break
        i += 1
    return i


def set_ansi_console() -> None:
    if sys.platform == "win32":
        import platform
        if platform.version() < '10.':
            raise RuntimeError(
                'ANSI console mode requires Windows 10 or higher, detected {}'.format(platform.version()))
        import ctypes
        # https://docs.microsoft.com/en-us/windows/console/getstdhandle
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        # https://docs.microsoft.com/en-us/windows/desktop/WinProg/windows-data-types#lpdword
        mode = ctypes.c_uint32()
        # https://docs.microsoft.com/en-us/windows/console/getconsolemode
        ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        mode.value |= 4  # add ENABLE_VIRTUAL_TERMINAL_PROCESSING
        # https://docs.microsoft.com/en-us/windows/console/setconsolemode
        ctypes.windll.kernel32.SetConsoleMode(handle, mode)
