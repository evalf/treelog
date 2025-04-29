from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Union


class Level(Enum):

    debug = 0
    info = 1
    user = 2
    warning = 3
    error = 4


@dataclass(frozen=True)
class Data:
    name: str
    data: bytes

    def __str__(self):
        return f'{self.name} [{len(self.data)} bytes]'


class Log(Protocol):

    def pushcontext(self, title: str) -> None: ...
    def popcontext(self) -> None: ...
    def recontext(self, title: str) -> None: ...
    def write(self, msg: Union[str, Data], level: Level) -> None: ...
