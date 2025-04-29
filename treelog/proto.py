from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Union, Optional


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
    type: Optional[str] = None

    def __str__(self):
        info = f'{len(self.data)} bytes'
        if self.type:
            info = f'{self.type}; {info}'
        return f'{self.name} [{info}]'


class Log(Protocol):

    def pushcontext(self, title: str) -> None: ...
    def popcontext(self) -> None: ...
    def recontext(self, title: str) -> None: ...
    def write(self, msg: Union[str, Data], level: Level) -> None: ...
