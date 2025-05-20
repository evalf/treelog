import sys

from .proto import Level, oldproto


def RichOutputLog(file=sys.stdout):
    set_ansi_console()
    return _RichOutputLog(file, prefix='', status=Status())


class Status:

    def __init__(self):
        self.c = []

    def add(self, prefix):
        self.c.append(prefix)

    def remove(self, prefix):
        self.c.remove(prefix)

    def __str__(self):
        # later, when we support simultaneously opened contexts, we can replace
        # this with something more sophisticated
        return max(self.c, default='')

    def print(self, file):
        file.write(f'\r{self}\033[K')
        file.flush()


@oldproto.fromnew
class _RichOutputLog:
    '''Output rich (colored,unicode) text to stream.'''

    _cmap = (
        '\033[1;30m',  # debug: bold gray
        '\033[1m',  # info: bold
        '\033[1;34m',  # user: bold blue
        '\033[1;35m',  # warning: bold purple
        '\033[1;31m')  # error: bold red

    def __init__(self, file, prefix, status) -> None:
        self.file = file
        self.prefix = prefix
        self.status = status
        status.add(prefix)
        status.print(file)

    def branch(self, title):
        return self.__class__(self.file, self.prefix + title + ' > ', self.status)

    def write(self, msg, level: Level) -> None:
        self.file.write(f'\r{self.prefix}{self._cmap[level.value]}{msg}\033[0m\033[K\n')
        self.status.print(self.file)

    def close(self):
        self.status.remove(self.prefix)
        self.status.print(self.file)


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
