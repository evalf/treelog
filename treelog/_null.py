import typing

from ._io import devnull
from .proto import Level


class NullLog:

    def pushcontext(self, title: str) -> None:
        pass

    def popcontext(self) -> None:
        pass

    def recontext(self, title: str) -> None:
        pass

    def write(self, text: str, level: Level) -> None:
        pass

    def open(self, filename: str, mode: str, level: Level) -> typing.ContextManager[typing.IO[typing.Any]]:
        return devnull(mode)
