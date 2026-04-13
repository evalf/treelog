import sys

from .proto import Level


class StdoutLog:
    """Output plain text to stream."""

    def __init__(self, file=sys.stdout, prefix=""):
        self.file = file
        self.prefix = prefix

    def branch(self, title):
        return StdoutLog(self.file, self.prefix + title + " > ")

    def write(self, msg, level: Level) -> None:
        if self.prefix:
            msg = self.prefix + str(msg).replace(
                "\n", "\n" + " > ".rjust(len(self.prefix))
            )
        print(msg, file=self.file, flush=True)

    def close(self):
        pass
