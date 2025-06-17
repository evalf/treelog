# Copyright (c) 2018 Evalf
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import doctest
import gc
import io
import os
import tempfile
import treelog
import unittest
import warnings

from treelog import _path, _state
from treelog.proto import Level, Data


@treelog.withcontext
def generate_test():
    'decorated function for unit testing'

    with treelog.warningfile('test.dat', 'wb') as f:
        f.write(b'test3')


def generate():
    'generate log events for unit testing'

    treelog.user('my message')
    with treelog.infofile('test.dat', 'w') as f:
        f.write('test1')
    with treelog.context('my context'):
        with treelog.iter.plain('iter', 'abc') as items:
            for c in items:
                treelog.info(c)
        with treelog.context('empty'):
            pass
        treelog.error('multiple..\n  ..lines')
        with treelog.userfile('test.dat', 'wb') as f:
            treelog.info('generating')
            f.write(b'test2')
    generate_test()
    with treelog.context('context step={}', 0) as format:
        treelog.info('foo')
        format(1)
        treelog.info('bar')
    treelog.errordata('same.dat', b'test3')
    with treelog.debugfile('dbg.jpg', 'wb', type='image/jpg') as f:
        f.write(b'test4')
    treelog.debug('dbg')
    treelog.warning('warn')


class StdoutLog(unittest.TestCase):

    def test_output(self):
        f = io.StringIO()
        with treelog.set(treelog.StdoutLog(f)):
            generate()
        self.check_output(f)

    def check_output(self, f):
        self.assertEqual(f.getvalue(),
           'my message\n'
           'test.dat [5 bytes]\n'
           'my context > iter 1 > a\n'
           'my context > iter 2 > b\n'
           'my context > iter 3 > c\n'
           'my context > multiple..\n'
           '  ..lines\n'
           'my context > test.dat > generating\n'
           'my context > test.dat [5 bytes]\n'
           'generate_test > test.dat [5 bytes]\n'
           'context step=0 > foo\n'
           'context step=1 > bar\n'
           'same.dat [5 bytes]\n'
           'dbg.jpg [image/jpg; 5 bytes]\n'
           'dbg\n'
           'warn\n')


class RichOutputLog(unittest.TestCase):

    def test_output(self):
        f = io.StringIO()
        with treelog.set(treelog.RichOutputLog(f)):
            generate()
        self.check_output(f)

    def check_output(self, f):
        self.assertEqual(f.getvalue().split('\r'), ['',
            '\x1b[K',
            '\x1b[1;34mmy message\x1b[0m\x1b[K\n',
            '\x1b[K',
            'test.dat > \x1b[K',
            '\x1b[K',
            '\x1b[1mtest.dat [5 bytes]\x1b[0m\x1b[K\n',
            '\x1b[K',
            'my context > \x1b[K',
            'my context > iter 0 > \x1b[K',
            'my context > \x1b[K',
            'my context > iter 1 > \x1b[K',
            'my context > iter 1 > \x1b[1ma\x1b[0m\x1b[K\n',
            'my context > iter 1 > \x1b[K',
            'my context > \x1b[K',
            'my context > iter 2 > \x1b[K',
            'my context > iter 2 > \x1b[1mb\x1b[0m\x1b[K\n',
            'my context > iter 2 > \x1b[K',
            'my context > \x1b[K',
            'my context > iter 3 > \x1b[K',
            'my context > iter 3 > \x1b[1mc\x1b[0m\x1b[K\n',
            'my context > iter 3 > \x1b[K',
            'my context > \x1b[K',
            'my context > empty > \x1b[K',
            'my context > \x1b[K',
            'my context > \x1b[1;31mmultiple..\n  ..lines\x1b[0m\x1b[K\n',
            'my context > \x1b[K',
            'my context > test.dat > \x1b[K',
            'my context > test.dat > \x1b[1mgenerating\x1b[0m\x1b[K\n',
            'my context > test.dat > \x1b[K',
            'my context > \x1b[K',
            'my context > \x1b[1;34mtest.dat [5 bytes]\x1b[0m\x1b[K\n',
            'my context > \x1b[K',
            '\x1b[K',
            'generate_test > \x1b[K',
            'generate_test > test.dat > \x1b[K',
            'generate_test > \x1b[K',
            'generate_test > \x1b[1;35mtest.dat [5 bytes]\x1b[0m\x1b[K\n',
            'generate_test > \x1b[K',
            '\x1b[K',
            'context step=0 > \x1b[K',
            'context step=0 > \x1b[1mfoo\x1b[0m\x1b[K\n',
            'context step=0 > \x1b[K',
            '\x1b[K',
            'context step=1 > \x1b[K',
            'context step=1 > \x1b[1mbar\x1b[0m\x1b[K\n',
            'context step=1 > \x1b[K',
            '\x1b[K',
            '\x1b[1;31msame.dat [5 bytes]\x1b[0m\x1b[K\n',
            '\x1b[K',
            'dbg.jpg > \x1b[K',
            '\x1b[K',
            '\x1b[1;30mdbg.jpg [image/jpg; 5 bytes]\x1b[0m\x1b[K\n',
            '\x1b[K',
            '\x1b[1;30mdbg\x1b[0m\x1b[K\n',
            '\x1b[K',
            '\x1b[1;35mwarn\x1b[0m\x1b[K\n',
            '\x1b[K'])


class DataLog(unittest.TestCase):

    def test_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with treelog.set(treelog.DataLog(tmpdir)):
                generate()
            self.check_output(tmpdir)

    def check_output(self, tmpdir):
        self.assertEqual(set(os.listdir(tmpdir)), {
                         'test.dat', 'test-1.dat', 'test-2.dat', 'same.dat', 'dbg.jpg'})
        with open(os.path.join(tmpdir, 'test.dat'), 'r') as f:
            self.assertEqual(f.read(), 'test1')
        with open(os.path.join(tmpdir, 'test-1.dat'), 'rb') as f:
            self.assertEqual(f.read(), b'test2')
        with open(os.path.join(tmpdir, 'test-2.dat'), 'rb') as f:
            self.assertEqual(f.read(), b'test3')
        with open(os.path.join(tmpdir, 'same.dat'), 'rb') as f:
            self.assertEqual(f.read(), b'test3')
        with open(os.path.join(tmpdir, 'dbg.jpg'), 'r') as f:
            self.assertEqual(f.read(), 'test4')

    @unittest.skipIf(not _path.supports_fd, 'dir_fd not supported on platform')
    def test_move_outdir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outdira = os.path.join(tmpdir, 'a')
            outdirb = os.path.join(tmpdir, 'b')
            log = treelog.DataLog(outdira)
            os.rename(outdira, outdirb)
            os.mkdir(outdira)
            log.write(Data('dat', b''), level=1)
            self.assertEqual(os.listdir(outdirb), ['dat'])
            self.assertEqual(os.listdir(outdira), [])


class HtmlLog(unittest.TestCase):

    def test_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with treelog.HtmlLog(tmpdir, title='test') as htmllog, treelog.set(htmllog):
                generate()
            self.check_output(tmpdir, htmllog.filename)

    def check_output(self, tmpdir, filename):
        self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'log', 'index.html')))
        self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'log', 'test-1.dat')))
        self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'log', 'my context', 'test-1.dat')))
        self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'log', 'dbg-1.jpg')))
        with open(os.path.join(tmpdir, 'log', 'index.html'), 'r') as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            '<html><head>\n',
            '<style>\n',
            'a, a:visited, a:hover, a:active { color: inherit; }\n',
            'li.d { color: gray; }\n',
            'li.i { color: green; }\n',
            'li.u { color: blue; }\n',
            'li.w { color: orange; }\n',
            'li.e { color: red; }\n',
            'li.o { list-style-type: circle; }\n',
            'li.o a { text-decoration: none; }\n',
            '</style>\n',
            '</head>\n',
            '<body><h1>test</h1><ul>\n',
            '<li class="u">my message</li>\n',
            '<li class="o"><a href="test.dat/index.html">test.dat</a></li>\n',
            '<li class="i"><a href="test-1.dat" download="test.dat">test.dat</a> [5 bytes]</li>\n',
            '<li class="o"><a href="my%20context/index.html">my context</a></li>\n',
            '<li class="o"><a href="generate_test/index.html">generate_test</a></li>\n',
            '<li class="o"><a href="context%20step%3D0/index.html">context step=0</a></li>\n',
            '<li class="o"><a href="context%20step%3D1/index.html">context step=1</a></li>\n',
            '<li class="e"><a href="same.dat" download="same.dat">same.dat</a> [5 bytes]</li>\n',
            '<li class="o"><a href="dbg.jpg/index.html">dbg.jpg</a></li>\n',
            '<li class="d"><a href="dbg-1.jpg" download="dbg.jpg">dbg.jpg</a> [5 bytes]<br><img src="dbg-1.jpg"></li>\n',
            '<li class="d">dbg</li>\n',
            '<li class="w">warn</li>\n',
            '</ul><p>closed.</p></body></html>\n',
        ])

    @unittest.skipIf(not _path.supports_fd, 'dir_fd not supported on platform')
    def test_move_outdir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outdira = os.path.join(tmpdir, 'a')
            outdirb = os.path.join(tmpdir, 'b')
            with treelog.HtmlLog(outdira, title='test') as log:
                os.rename(outdira, outdirb)
                os.mkdir(outdira)
                log.write(Data('dat', b''), Level.info)
            self.assertTrue(os.path.isfile, os.path.join(outdirb, 'index.html'))

    def test_filename_sequence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with treelog.HtmlLog(tmpdir, title='test') as log:
                pass
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'log', 'index.html')))
            with treelog.HtmlLog(tmpdir, title='test') as log:
                pass
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'log-1', 'index.html')))
            with treelog.HtmlLog(tmpdir, title='test') as log:
                pass
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, 'log-2', 'index.html')))


class RecordLog(unittest.TestCase):

    def test_output(self):
        recordlog = treelog.RecordLog()
        with treelog.set(recordlog):
            generate()
        self.check_output(recordlog.current)
        with self.subTest('replay to StdoutLog'):
            f = io.StringIO()
            recordlog.replay(treelog.StdoutLog(f))
            StdoutLog.check_output(self, f)
        with self.subTest('replay to DataLog'), tempfile.TemporaryDirectory() as tmpdir:
            recordlog.replay(treelog.DataLog(tmpdir))
            DataLog.check_output(self, tmpdir)
        with self.subTest('replay to HtmlLog'), tempfile.TemporaryDirectory() as tmpdir:
            with treelog.HtmlLog(tmpdir, title='test') as htmllog:
                recordlog.replay(htmllog)
            HtmlLog.check_output(self, tmpdir, htmllog.filename)
        with self.subTest('replay to RichOutputLog'):
            f = io.StringIO()
            recordlog.replay(treelog.RichOutputLog(f))
            RichOutputLog.check_output(self, f)

    def check_output(self, messages):
        self.assertEqual(messages, [
            ('my message', Level.user),
            ('test.dat', []),
            (Data(name='test.dat', data=b'test1', type=None), Level.info),
            ('my context', [
                ('iter 0', []),
                ('iter 1', [('a', Level.info)]),
                ('iter 2', [('b', Level.info)]),
                ('iter 3', [('c', Level.info)]),
                ('empty', []),
                ('multiple..\n  ..lines', Level.error),
                ('test.dat', [('generating', Level.info)]),
                (Data(name='test.dat', data=b'test2', type=None), Level.user),
            ]),
            ('generate_test', [
                ('test.dat', []),
                (Data(name='test.dat', data=b'test3', type=None), Level.warning),
            ]),
            ('context step=0', [
                ('foo', Level.info),
            ]),
            ('context step=1', [
                ('bar', Level.info),
            ]),
            (Data(name='same.dat', data=b'test3', type=None), Level.error),
            ('dbg.jpg', []),
            (Data(name='dbg.jpg', data=b'test4', type='image/jpg'), Level.debug),
            ('dbg', Level.debug),
            ('warn', Level.warning),
        ])

    def test_replay_in_current(self):
        recordlog = treelog.RecordLog()
        recordlog.write('test', level=Level.info)
        with treelog.set(treelog.LoggingLog()), self.assertLogs('nutils'):
            recordlog.replay()


class TeeLog(unittest.TestCase):

    def test_output(self):
        f = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            datalog = treelog.DataLog(tmpdir)
            recordlog = treelog.RecordLog(simplify=False)
            richoutputlog = treelog.RichOutputLog(f)
            with treelog.set(treelog.TeeLog(richoutputlog, treelog.TeeLog(datalog, recordlog))):
                generate()
            with self.subTest('DataLog'):
                DataLog.check_output(self, tmpdir)
            with self.subTest('RecordLog'):
                RecordLog.check_output(self, recordlog.current)
            with self.subTest('RichOutputLog'):
                RichOutputLog.check_output(self, f)

    def test_open_datalog_datalog_samedir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            teelog = treelog.TeeLog(treelog.DataLog(
                tmpdir), treelog.DataLog(tmpdir))
            teelog.write(Data('test', b'test'), Level.info)
            with open(os.path.join(tmpdir, 'test'), 'rb') as f:
                self.assertEqual(f.read(), b'test')
            with open(os.path.join(tmpdir, 'test-1'), 'rb') as f:
                self.assertEqual(f.read(), b'test')


class FilterMinLog(unittest.TestCase):

    def test_output(self):
        recordlog = treelog.RecordLog()
        with treelog.set(treelog.FilterLog(recordlog, minlevel=Level.user)):
            generate()
        self.check_output(recordlog.current)

    def check_output(self, messages):
        self.assertEqual(messages, [
            ('my message', Level.user),
            ('test.dat', []),
            ('my context', [
                ('iter 0', []),
                ('iter 1', []),
                ('iter 2', []),
                ('iter 3', []),
                ('empty', []),
                ('multiple..\n  ..lines', Level.error),
                ('test.dat', []),
                (Data(name='test.dat', data=b'test2', type=None), Level.user),
            ]),
            ('generate_test', [
                ('test.dat', []),
                (Data(name='test.dat', data=b'test3', type=None), Level.warning),
            ]),
            ('context step=0', []),
            ('context step=1', []),
            (Data(name='same.dat', data=b'test3', type=None), Level.error),
            ('dbg.jpg', []), ('warn', Level.warning),
        ])


class FilterMaxLog(unittest.TestCase):

    def test_output(self):
        recordlog = treelog.RecordLog()
        with treelog.set(treelog.FilterLog(recordlog, maxlevel=Level.user)):
            generate()
        self.check_output(recordlog.current)

    def check_output(self, messages):
        self.assertEqual(messages, [
            ('my message', Level.user),
            ('test.dat', []),
            (Data(name='test.dat', data=b'test1', type=None), Level.info),
            ('my context', [
                ('iter 0', []),
                ('iter 1', [('a', Level.info)]),
                ('iter 2', [('b', Level.info)]),
                ('iter 3', [('c', Level.info)]),
                ('empty', []),
                ('test.dat', [('generating', Level.info)]),
                (Data(name='test.dat', data=b'test2', type=None), Level.user),
            ]),
            ('generate_test', [
                ('test.dat', []),
            ]),
            ('context step=0', [
                ('foo', Level.info),
            ]),
            ('context step=1', [
                ('bar', Level.info),
            ]),
            ('dbg.jpg', []),
            (Data(name='dbg.jpg', data=b'test4', type='image/jpg'), Level.debug),
            ('dbg', Level.debug),
        ])


class FilterMinMaxLog(unittest.TestCase):

    def test_output(self):
        recordlog = treelog.RecordLog()
        with treelog.set(treelog.FilterLog(recordlog, minlevel=Level.info, maxlevel=Level.warning)):
            generate()
        self.check_output(recordlog.current)

    def check_output(self, messages):
        self.assertEqual(messages, [
            ('my message', Level.user),
            ('test.dat', []),
            (Data(name='test.dat', data=b'test1', type=None), Level.info),
            ('my context', [
                ('iter 0', []),
                ('iter 1', [('a', Level.info)]),
                ('iter 2', [('b', Level.info)]),
                ('iter 3', [('c', Level.info)]),
                ('empty', []),
                ('test.dat', [('generating', Level.info)]),
                (Data(name='test.dat', data=b'test2', type=None), Level.user),
            ]),
            ('generate_test', [('test.dat', []), (Data(name='test.dat', data=b'test3', type=None), Level.warning)]),
            ('context step=0', [
                ('foo', Level.info),
            ]),
            ('context step=1', [
                ('bar', Level.info),
            ]),
            ('dbg.jpg', []),
            ('warn', Level.warning),
        ])


class LoggingLog(unittest.TestCase):

    def test_output(self):
        with self.assertLogs('nutils') as cm, treelog.set(treelog.LoggingLog()):
            generate()
        self.check_output(cm.output)

    def check_output(self, output):
        self.assertEqual(output, [
            'Level 25:nutils:my message',
            'INFO:nutils:test.dat [5 bytes]',
            'INFO:nutils:my context > iter 1 > a',
            'INFO:nutils:my context > iter 2 > b',
            'INFO:nutils:my context > iter 3 > c',
            'ERROR:nutils:my context > multiple..\n  ..lines',
            'INFO:nutils:my context > test.dat > generating',
            'Level 25:nutils:my context > test.dat [5 bytes]',
            'WARNING:nutils:generate_test > test.dat [5 bytes]',
            'INFO:nutils:context step=0 > foo',
            'INFO:nutils:context step=1 > bar',
            'ERROR:nutils:same.dat [5 bytes]',
            'WARNING:nutils:warn'])


class NullLog(unittest.TestCase):

    def test_output(self):
        with treelog.set(treelog.NullLog()):
            generate()

    def test_disable(self):
        with treelog.disable():
            self.assertIsInstance(_state.current, treelog.NullLog)


class Iter(unittest.TestCase):

    def setUp(self):
        self.recordlog = treelog.RecordLog(simplify=False)
        c = treelog.set(self.recordlog)
        c.__enter__()
        self.addCleanup(c.__exit__, None, None, None)

    def assertMessages(self, *msg):
        self.assertEqual(self.recordlog.current, list(msg))

    def test_context(self):
        with treelog.iter.plain('test', enumerate('abc')) as myiter:
            for i, c in myiter:
                self.assertEqual(c, 'abc'[i])
                treelog.info('hi')
        self.assertMessages(
            ('test 0', []),
            ('test 1', [('hi', Level.info)]),
            ('test 2', [('hi', Level.info)]),
            ('test 3', [('hi', Level.info)]))

    def test_nocontext(self):
        for i, c in treelog.iter.plain('test', enumerate('abc')):
            self.assertEqual(c, 'abc'[i])
            treelog.info('hi')
        self.assertMessages(
            ('test 0', []),
            ('test 1', [('hi', Level.info)]),
            ('test 2', [('hi', Level.info)]),
            ('test 3', [('hi', Level.info)]))

    def test_break_entered(self):
        with warnings.catch_warnings(record=True) as w, treelog.iter.plain('test', [1, 2, 3]) as myiter:
            for item in myiter:
                self.assertEqual(item, 1)
                treelog.info('hi')
                break
            gc.collect()
        self.assertEqual(w, [])
        self.assertMessages(
            ('test 0', []),
            ('test 1', [('hi', Level.info)]))

    def test_break_notentered(self):
        with self.assertWarns(ResourceWarning):
            for item in treelog.iter.plain('test', [1, 2, 3]):
                self.assertEqual(item, 1)
                treelog.info('hi')
                break
            gc.collect()
        self.assertMessages(
            ('test 0', []),
            ('test 1', [('hi', Level.info)]))

    def test_multiple(self):
        with treelog.iter.plain('test', 'abc', [1, 2]) as items:
            self.assertEqual(list(items), [('a', 1), ('b', 2)])

    def test_plain(self):
        with treelog.iter.plain('test', 'abc') as items:
            self.assertEqual(list(items), list('abc'))
        self.assertMessages(
            ('test 0', []),
            ('test 1', []),
            ('test 2', []),
            ('test 3', []))

    def test_plain_withbraces(self):
        with treelog.iter.plain('t{es}t', 'abc') as items:
            self.assertEqual(list(items), list('abc'))
        self.assertMessages(
            ('t{es}t 0', []),
            ('t{es}t 1', []),
            ('t{es}t 2', []),
            ('t{es}t 3', []))

    def test_fraction(self):
        with treelog.iter.fraction('test', 'abc') as items:
            self.assertEqual(list(items), list('abc'))
        self.assertMessages(
            ('test 0/3', []),
            ('test 1/3', []),
            ('test 2/3', []),
            ('test 3/3', []))

    def test_percentage(self):
        with treelog.iter.percentage('test', 'abc') as items:
            self.assertEqual(list(items), list('abc'))
        self.assertMessages(
            ('test 0%', []),
            ('test 33%', []),
            ('test 67%', []),
            ('test 100%', []))

    def test_send(self):
        def titles():
            a = yield 'value'
            while True:
                a = yield 'value={!r}'.format(a)
        with treelog.iter.wrap(titles(), 'abc') as items:
            for i, item in enumerate(items):
                self.assertEqual(item, 'abc'[i])
            treelog.info('hi')
        self.assertMessages(
            ('value', []),
            ("value='a'", []),
            ("value='b'", []),
            ("value='c'", [('hi', Level.info)]))


class Path(unittest.TestCase):

    def setUp(self):
        c = tempfile.TemporaryDirectory()
        self.tmpdir = c.__enter__()
        self.addCleanup(c.__exit__, None, None, None)
        self.path = _path.makedirs(self.tmpdir, 'foo')

    def test_open(self):
        with (self.path / 'testfile').open('w') as f:
            f.write('hi!')
        with open(os.path.join(self.tmpdir, 'foo', 'testfile')) as f:
            self.assertEqual(f.read(), 'hi!')

    def test_mkdir(self):
        d = (self.path / 'testdir').mkdir()
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, 'foo', 'testdir')))
        with self.assertRaises(FileExistsError):
            (self.path / 'testdir').mkdir()
        (self.path / 'testdir').mkdir(exist_ok=True)
        with self.assertRaises(FileNotFoundError):
            (self.path / 'a' / 'b').mkdir()
        (self.path / 'a' / 'b').mkdir(parents=True)
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, 'foo', 'a', 'b')))

    @unittest.skipIf(not _path.supports_fd, 'dir_fd not supported on platform')
    def test_move(self):
        os.rename(os.path.join(self.tmpdir, 'foo'), os.path.join(self.tmpdir, 'bar'))
        with (self.path / 'testfile').open('w') as f:
            pass
        self.assertTrue(os.path.isfile(os.path.join(self.tmpdir, 'bar', 'testfile')))
        (self.path / 'testdir').mkdir()
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, 'bar', 'testdir')))


class DocTest(unittest.TestCase):

    def test_docs(self):
        doctest.testmod(treelog)


# vim:sw=4:sts=4:et
