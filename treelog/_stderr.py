import sys

from ._context import ContextLog
from .proto import Level


class StderrLog(ContextLog):
    '''Output plain text to stream.'''

    def write(self, text: str, level: Level) -> None:
        print(' > '.join((*self.currentcontext, text)), file=sys.stderr)
