from . import proto
from ._context import ContextLog


class StdoutLog(ContextLog):
    '''Output plain text to stream.'''

    def write(self, text: str, level: proto.Level) -> None:
        print(' > '.join((*self.currentcontext, text)))
