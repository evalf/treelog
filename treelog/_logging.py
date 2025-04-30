from typing import Optional
import logging

from ._context import ContextLog
from .proto import Level


class LoggingLog(ContextLog):
    '''Log to Python's built-in logging facility.'''

    _levels = logging.DEBUG, logging.INFO, 25, logging.WARNING, logging.ERROR

    def __init__(self, name: str = 'nutils') -> None:
        self._logger = logging.getLogger(name)
        super().__init__()

    def write(self, msg, level: Level, data: Optional[bytes] = None) -> None:
        self._logger.log(self._levels[level.value], ' > '.join(
            (*self.currentcontext, str(msg))))
