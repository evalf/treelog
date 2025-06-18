import contextlib
import html
import os
import urllib.parse
import contextlib

from ._path import makedirs, sequence, non_existent
from .proto import Level, Data


def HtmlLog(dirpath: str, *, title: str, **_):
    name, path = non_existent(dirpath, sequence('log'), lambda p: makedirs(p, exist_ok=False))
    log = _HtmlLog(path, title)
    log.filename = os.path.join(name, 'index.html') # for backwards compatibility
    return contextlib.closing(log)


class _HtmlLog:
    '''Output html nested lists.'''

    def __init__(self, path: 'Path', title: str):
        self._path = path
        self._html = (path / 'index.html').open('x')
        print(f'<html>{HEAD}<body><h1>{title}</h1><ul>', file=self._html)
        self._running()

    def _running(self):
        self._pos = self._html.tell()
        print('</ul><p>running (reload to refresh)</p></body></html>', file=self._html, flush=True)

    def _li(self, cls, inner):
        self._html.seek(self._pos)
        print(f'<li class="{cls}">{inner}</li>', file=self._html)
        self._running()

    def branch(self, title):
        dirname, _ = non_existent(self._path, sequence(title), lambda p: p.mkdir(exist_ok=False))
        self._li('o', f'<a href="{urllib.parse.quote(dirname)}/index.html">{html.escape(title)}</a>')
        return self.__class__(self._path / dirname, title=title)

    def write(self, msg, level: Level) -> None:
        if not isinstance(msg, Data):
            text = html.escape(msg)
        else:
            filename, f = non_existent(self._path, sequence(msg.name), lambda p: p.open('xb'))
            with f:
                f.write(msg.data)
            text = f'<a href="{urllib.parse.quote(filename)}" download="{urllib.parse.quote(msg.name)}">{html.escape(msg.name)}</a> [{len(msg.data)} bytes]'
            if msg.name.endswith('.jpg') or msg.name.endswith('.png'):
                text += f'<br><img src="{urllib.parse.quote(filename)}">'
        self._li(level.name[0], text)

    def close(self):
        self._html.seek(self._pos)
        self._html.truncate()
        print('</ul><p>closed.</p></body></html>', file=self._html)
        self._html.close()


HEAD = '''\
<head>
<style>
a, a:visited, a:hover, a:active { color: inherit; }
li.d { color: gray; }
li.i { color: green; }
li.u { color: blue; }
li.w { color: orange; }
li.e { color: red; }
li.o { list-style-type: circle; }
li.o a { text-decoration: none; }
</style>
</head>
'''
