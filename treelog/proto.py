import typing
import typing_extensions
import enum


class Level(enum.Enum):

    debug = 0
    info = 1
    user = 2
    warning = 3
    error = 4


class Log(typing_extensions.Protocol):

    def pushcontext(self, title: str) -> None: ...
    def popcontext(self) -> None: ...
    def recontext(self, title: str) -> None: ...
    def write(self, text: str, level: Level) -> None: ...

    def open(self, filename: str, mode: str,
             level: Level) -> typing_extensions.ContextManager[typing.IO[typing.Any]]: ...
