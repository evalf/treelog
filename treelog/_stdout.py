import sys

from .proto import Level, oldproto


@oldproto.fromnew
class StdoutLog:
    '''Output plain text to stream.'''

    def __init__(self, file=sys.stdout, prefix=''):
        self.file = file
        self.prefix = prefix

    def branch(self, title):
        return self.__class__(self.file, self.prefix + title + ' > ')

    def write(self, msg, level: Level) -> None:
        print(self.prefix, msg, sep='', file=self.file, flush=True)

    def close(self):
        pass
