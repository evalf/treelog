from typing import Callable, Iterable, Optional
import functools
import os

from ._path import makedirs, sequence
from .proto import Level, Data


class DataLog:
    '''Output only data.'''

    def __init__(self, dirpath: str = os.curdir, names: Callable[[str], Iterable[str]] = sequence) -> None:
        self._names = functools.lru_cache(maxsize=32)(names)
        self._path = makedirs(dirpath)

    def pushcontext(self, title: str, length: Optional[int] = None) -> None:
        pass

    def popcontext(self) -> None:
        pass

    def nextiter(self) -> None:
        pass

    def write(self, msg, level: Level) -> None:
        if isinstance(msg, Data):
            for filename in self._names(msg.name):
                try:
                    f = (self._path / filename).open('xb')
                except FileExistsError:
                    continue
                break
            else:
                raise ValueError('all filenames are in use')
            with f:
                f.write(msg.data)
