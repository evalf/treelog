import sys

from . import proto


class StdoutLog:
    '''Output plain text to stream.'''

    def __init__(self, file=sys.stdout):
        self.file = file
        self.currentcontext = []  # type: typing.List[str]

    def pushcontext(self, title: str) -> None:
        self.currentcontext.append(title + ' > ')

    def popcontext(self) -> None:
        self.currentcontext.pop()

    def recontext(self, title: str) -> None:
        self.currentcontext[-1] = title + ' > '

    def write(self, msg, level: proto.Level) -> None:
        if self.currentcontext:
            prefix = ''.join(self.currentcontext)
            msg = prefix + str(msg).replace('\n', '\n' + ' > '.rjust(len(prefix)))
        print(msg, file=self.file)
