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

    @property
    def info(self):
        info = f"{len(self.data)} bytes"
        if self.type:
            info = f"{self.type}; {info}"
        return info

    def __str__(self):
        return f"{self.name} [{self.info}]"


@dataclass(frozen=True)
class Iter:
    name: str
    index: int
    length: int

    def __str__(self):
        return f"{self.name} {self.index + 1}/{self.length}"


class Log(Protocol):
    def pushcontext(self, title: Union[str, Iter]) -> None: ...
    def popcontext(self) -> None: ...
    def recontext(self, title: Union[str, Iter]) -> None: ...
    def write(self, msg: Union[str, Data], level: Level) -> None: ...
