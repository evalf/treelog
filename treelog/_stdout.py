from . import proto
from ._context import ContextLog


class StdoutLog(ContextLog):
    '''Output plain text to stream.'''

    def write(self, msg, level: proto.Level) -> None:
        print(*self.currentcontext, msg, sep=' > ')
