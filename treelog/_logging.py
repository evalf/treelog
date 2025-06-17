import logging

from .proto import Level


def LoggingLog(name: str = 'nutils'):
    return _LoggingLog(logging.getLogger(name), prefix='')


class _LoggingLog:
    '''Output plain text to stream.'''

    _levels = logging.DEBUG, logging.INFO, 25, logging.WARNING, logging.ERROR

    def __init__(self, logger, prefix):
        self._logger = logger
        self._prefix = prefix

    def branch(self, title):
        return self.__class__(self._logger, self._prefix + title + ' > ')

    def write(self, msg, level) -> None:
        self._logger.log(self._levels[level.value], self._prefix + str(msg))

    def close(self):
        pass
