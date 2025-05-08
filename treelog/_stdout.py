import sys

from . import proto
from ._context import ContextLog


class StdoutLog(ContextLog):
    '''Output plain text to stream.'''

    def __init__(self, file=sys.stdout):
        self.file = file
        super().__init__()

    def write(self, msg, level: proto.Level) -> None:
        print(*self.currentcontext, msg, sep=' > ', file=self.file)
