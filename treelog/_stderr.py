import sys

from ._context import ContextLog
from .proto import Level


class StderrLog(ContextLog):
    '''Output plain text to stream.'''

    def write(self, msg, level: Level) -> None:
        print(*self.currentcontext, msg, sep=' > ', file=sys.stderr)
