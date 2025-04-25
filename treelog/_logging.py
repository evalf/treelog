import logging
import typing

from ._context import ContextLog
from .proto import Level


class LoggingLog(ContextLog):
    '''Log to Python's built-in logging facility.'''

    # type: typing.ClassVar[typing.Tuple[int, int, int, int, int]]
    _levels = logging.DEBUG, logging.INFO, 25, logging.WARNING, logging.ERROR

    def __init__(self, name: str = 'nutils') -> None:
        self._logger = logging.getLogger(name)
        super().__init__()

    def write(self, text: str, level: Level) -> None:
        self._logger.log(self._levels[level.value], ' > '.join(
            (*self.currentcontext, text)))
