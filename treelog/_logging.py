import logging
import typing

from .proto import Level


class LoggingLog:
    '''Log to Python's built-in logging facility.'''

    # type: typing.ClassVar[typing.Tuple[int, int, int, int, int]]
    _levels = logging.DEBUG, logging.INFO, 25, logging.WARNING, logging.ERROR

    def __init__(self, name: str = 'nutils') -> None:
        self._logger = logging.getLogger(name)
        self.currentcontext = []  # type: typing.List[str]

    def pushcontext(self, title: str) -> None:
        self.currentcontext.append(title)

    def popcontext(self) -> None:
        self.currentcontext.pop()

    def recontext(self, title: str) -> None:
        self.currentcontext[-1] = title

    def write(self, msg, level: Level, data: typing.Optional[bytes] = None) -> None:
        self._logger.log(self._levels[level.value], ' > '.join(
            (*self.currentcontext, str(msg))))
