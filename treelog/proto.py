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


# TRANSITIONAL, TEMPORARY
class oldproto:
    @classmethod
    def fromnew(cls, NewLog):
        return type(NewLog.__name__, (cls,), {'wrapped': NewLog})
    def __init__(self, *args, **kwargs):
        self.context = [self.wrapped(*args, **kwargs)]
    @property
    def current(self):
        return self.context[-1]
    def pushcontext(self, title):
        self.context.append(self.current.branch(title))
    def popcontext(self):
        self.context.pop().close()
    def recontext(self, title):
        self.popcontext()
        self.pushcontext(title)
    def write(self, msg, level):
        self.current.write(msg, level)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.context.pop().close()
        assert not self.context
    def __getattr__(self, attr):
        return getattr(self.context[0], attr)
