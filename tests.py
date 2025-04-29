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

import treelog
import unittest
import contextlib
import tempfile
import os
import sys
import hashlib
import io
import warnings
import gc
import doctest

from treelog import _path, _state
from treelog.proto import Level, Data


class Log(unittest.TestCase):

    maxDiff = None

    @contextlib.contextmanager
    def assertSilent(self):
        with capture() as captured:
            yield
        self.assertEqual(captured.stdout, '')

    @treelog.withcontext
    def generate_test(self):
        with treelog.warningfile('test.dat', 'wb') as f:
            f.write(b'test3')

    def generate(self):
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
        self.generate_test()
        with treelog.context('context step={}', 0) as format:
            treelog.info('foo')
            format(1)
            treelog.info('bar')
        with treelog.errorfile('same.dat', 'wb') as f:
            f.write(b'test3')
        with treelog.debugfile('dbg.dat', 'wb') as f:
            f.write(b'test4')
        treelog.debug('dbg')
        treelog.warning('warn')

    def test_output(self):
        with self.assertSilent(), self.output_tester() as log, treelog.set(log):
            self.generate()


class StdoutLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        with capture() as captured:
            yield treelog.StdoutLog()
        self.assertEqual(captured.stdout,
                         'my message\n'
                         'test.dat\n'
                         'my context > iter 1 > a\n'
                         'my context > iter 2 > b\n'
                         'my context > iter 3 > c\n'
                         'my context > multiple..\n'
                         '  ..lines\n'
                         'my context > test.dat > generating\n'
                         'my context > test.dat\n'
                         'generate_test > test.dat\n'
                         'context step=0 > foo\n'
                         'context step=1 > bar\n'
                         'same.dat\n'
                         'dbg.dat\n'
                         'dbg\n'
                         'warn\n')
        self.assertEqual(captured.stderr, '')


class StderrLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        with capture() as captured:
            yield treelog.StderrLog()
        self.assertEqual(captured.stderr,
                         'my message\n'
                         'test.dat\n'
                         'my context > iter 1 > a\n'
                         'my context > iter 2 > b\n'
                         'my context > iter 3 > c\n'
                         'my context > multiple..\n'
                         '  ..lines\n'
                         'my context > test.dat > generating\n'
                         'my context > test.dat\n'
                         'generate_test > test.dat\n'
                         'context step=0 > foo\n'
                         'context step=1 > bar\n'
                         'same.dat\n'
                         'dbg.dat\n'
                         'dbg\n'
                         'warn\n')
        self.assertEqual(captured.stdout, '')


class RichOutputLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        with capture() as captured:
            yield treelog.RichOutputLog()
        self.assertEqual(captured.stdout,
                         '\x1b[1;34mmy message\x1b[0m\n'
                         'test.dat > '
                         '\r\x1b[K'
                         '\x1b[1mtest.dat\x1b[0m\n'
                         'my context > '
                         'iter 0 '
                         '> \x1b[4D1 > '
                         '\x1b[1ma\x1b[0m\nmy context > iter 1 > '
                         '\x1b[4D2 > '
                         '\x1b[1mb\x1b[0m\nmy context > iter 2 > '
                         '\x1b[4D3 > '
                         '\x1b[1mc\x1b[0m\nmy context > iter 3 > '
                         '\x1b[9D\x1b[K'
                         'empty > '
                         '\x1b[8D\x1b[K'
                         '\x1b[1;31mmultiple..\n  ..lines\x1b[0m\nmy context > test.dat > '
                         '\x1b[1mgenerating\x1b[0m\nmy context > test.dat > '
                         '\x1b[11D\x1b[K'
                         '\x1b[1;34mtest.dat\x1b[0m\nmy context > '
                         '\r\x1b[Kgenerate_test > test.dat > '
                         '\x1b[11D\x1b[K'
                         '\x1b[1;35mtest.dat\x1b[0m\ngenerate_test > '
                         '\r\x1b[K'
                         'context step=0 > '
                         '\x1b[1mfoo\x1b[0m\n'
                         'context step=0 > '
                         '\x1b[4D1 > '
                         '\x1b[1mbar\x1b[0m\n'
                         'context step=1 > '
                         '\r\x1b[K'
                         'same.dat > '
                         '\r\x1b[K'
                         '\x1b[1;31msame.dat\x1b[0m\n'
                         'dbg.dat > '
                         '\r\x1b[K'
                         '\x1b[1;30mdbg.dat\x1b[0m\n'
                         '\x1b[1;30mdbg\x1b[0m\n'
                         '\x1b[1;35mwarn\x1b[0m\n')


class DataLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield treelog.DataLog(tmpdir)
            self.assertEqual(set(os.listdir(tmpdir)), {
                             'test.dat', 'test-1.dat', 'test-2.dat', 'same.dat', 'dbg.dat'})
            with open(os.path.join(tmpdir, 'test.dat'), 'r') as f:
                self.assertEqual(f.read(), 'test1')
            with open(os.path.join(tmpdir, 'test-1.dat'), 'rb') as f:
                self.assertEqual(f.read(), b'test2')
            with open(os.path.join(tmpdir, 'test-2.dat'), 'rb') as f:
                self.assertEqual(f.read(), b'test3')
            with open(os.path.join(tmpdir, 'same.dat'), 'rb') as f:
                self.assertEqual(f.read(), b'test3')
            with open(os.path.join(tmpdir, 'dbg.dat'), 'r') as f:
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


class HtmlLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tests = ['b444ac06613fc8d63795be9ad0beaf55011936ac.dat', '109f4b3c50d7b0df729d299bc6f8e9ef9066971f.dat',
                     '3ebfa301dc59196f18593c45e519287a23297589.dat', '1ff2b3704aede04eecb51e50ca698efd50a1379b.dat']
            with self.assertSilent(), treelog.HtmlLog(tmpdir, title='test') as htmllog:
                yield htmllog
            self.assertEqual(htmllog.filename, 'log.html')
            self.assertGreater(set(os.listdir(tmpdir)), {'log.html', *tests})
            with open(os.path.join(tmpdir, 'log.html'), 'r') as f:
                lines = f.readlines()
            self.assertIn('<body>\n', lines)
            self.assertEqual(lines[lines.index('<body>\n'):], [
                '<body>\n',
                '<div id="header"><div id="bar"><div id="text"><div id="title">test</div></div></div></div>\n',
                '<div id="log">\n',
                '<div class="item" data-loglevel="2">my message</div>\n',
                '<div class="item" data-loglevel="1"><a href="b444ac06613fc8d63795be9ad0beaf55011936ac.dat" download="test.dat">test.dat</a></div>\n',
                '<div class="context"><div class="title">my context</div><div class="children">\n',
                '<div class="context"><div class="title">iter 1</div><div class="children">\n',
                '<div class="item" data-loglevel="1">a</div>\n',
                '</div><div class="end"></div></div>\n',
                '<div class="context"><div class="title">iter 2</div><div class="children">\n',
                '<div class="item" data-loglevel="1">b</div>\n',
                '</div><div class="end"></div></div>\n',
                '<div class="context"><div class="title">iter 3</div><div class="children">\n',
                '<div class="item" data-loglevel="1">c</div>\n',
                '</div><div class="end"></div></div>\n',
                '<div class="item" data-loglevel="4">multiple..\n',
                '  ..lines</div>\n',
                '<div class="context"><div class="title">test.dat</div><div class="children">\n',
                '<div class="item" data-loglevel="1">generating</div>\n',
                '</div><div class="end"></div></div>\n',
                '<div class="item" data-loglevel="2"><a href="109f4b3c50d7b0df729d299bc6f8e9ef9066971f.dat" download="test.dat">test.dat</a></div>\n',
                '</div><div class="end"></div></div>\n',
                '<div class="context"><div class="title">generate_test</div><div class="children">\n',
                '<div class="item" data-loglevel="3"><a href="3ebfa301dc59196f18593c45e519287a23297589.dat" download="test.dat">test.dat</a></div>\n',
                '</div><div class="end"></div></div>\n',
                '<div class="context"><div class="title">context step=0</div><div '
                'class="children">\n',
                '<div class="item" data-loglevel="1">foo</div>\n',
                '</div><div class="end"></div></div>\n',
                '<div class="context"><div class="title">context step=1</div><div '
                'class="children">\n',
                '<div class="item" data-loglevel="1">bar</div>\n',
                '</div><div class="end"></div></div>\n',
                '<div class="item" data-loglevel="4"><a href="3ebfa301dc59196f18593c45e519287a23297589.dat" download="same.dat">same.dat</a></div>\n',
                '<div class="item" data-loglevel="0"><a href="1ff2b3704aede04eecb51e50ca698efd50a1379b.dat" download="dbg.dat">dbg.dat</a></div>\n',
                '<div class="item" data-loglevel="0">dbg</div>\n',
                '<div class="item" data-loglevel="3">warn</div>\n',
                '</div></body></html>\n'])
            for i, test in enumerate(tests, 1):
                with open(os.path.join(tmpdir, test), 'rb') as f:
                    self.assertEqual(f.read(), b'test%i' % i)

    @unittest.skipIf(not _path.supports_fd, 'dir_fd not supported on platform')
    def test_move_outdir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outdira = os.path.join(tmpdir, 'a')
            outdirb = os.path.join(tmpdir, 'b')
            with silent(), treelog.HtmlLog(outdira) as log:
                os.rename(outdira, outdirb)
                os.mkdir(outdira)
                log.write(Data('dat', b''), Level.info)
            self.assertIn(
                'da39a3ee5e6b4b0d3255bfef95601890afd80709', os.listdir(outdirb))

    def test_filename_sequence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with silent(), treelog.HtmlLog(tmpdir) as log:
                pass
            self.assertTrue(os.path.exists(os.path.join(tmpdir, 'log.html')))
            with silent(), treelog.HtmlLog(tmpdir) as log:
                pass
            self.assertTrue(os.path.exists(os.path.join(tmpdir, 'log-1.html')))
            with silent(), treelog.HtmlLog(tmpdir) as log:
                pass
            self.assertTrue(os.path.exists(os.path.join(tmpdir, 'log-2.html')))


class RecordLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        recordlog = treelog.RecordLog(simplify=False)
        yield recordlog
        self.assertEqual(recordlog._messages, [
            ('write', 'my message', Level.user),
            ('pushcontext', 'test.dat'),
            ('popcontext',),
            ('write', Data('test.dat', b'test1'), Level.info),
            ('pushcontext', 'my context'),
            ('pushcontext', 'iter 0'),
            ('recontext', 'iter 1'),
            ('write', 'a', Level.info),
            ('recontext', 'iter 2'),
            ('write', 'b', Level.info),
            ('recontext', 'iter 3'),
            ('write', 'c', Level.info),
            ('popcontext',),
            ('pushcontext', 'empty'),
            ('popcontext',),
            ('write', 'multiple..\n  ..lines', Level.error),
            ('pushcontext', 'test.dat'),
            ('write', 'generating', Level.info),
            ('popcontext',),
            ('write', Data('test.dat', b'test2'), Level.user),
            ('popcontext',),
            ('pushcontext', 'generate_test'),
            ('pushcontext', 'test.dat'),
            ('popcontext',),
            ('write', Data('test.dat', b'test3'), Level.warning),
            ('popcontext',),
            ('pushcontext', 'context step=0'),
            ('write', 'foo', Level.info),
            ('recontext', 'context step=1'),
            ('write', 'bar', Level.info),
            ('popcontext',),
            ('pushcontext', 'same.dat'),
            ('popcontext',),
            ('write', Data('same.dat', b'test3'), Level.error),
            ('pushcontext', 'dbg.dat'),
            ('popcontext',),
            ('write', Data('dbg.dat', b'test4'), Level.debug),
            ('write', 'dbg', Level.debug),
            ('write', 'warn', Level.warning)])
        for Log in StdoutLog, DataLog, HtmlLog, RichOutputLog:
            with self.subTest('replay to {}'.format(Log.__name__)), Log.output_tester(self) as log:
                recordlog.replay(log)

    def test_replay_in_current(self):
        recordlog = treelog.RecordLog()
        recordlog.write('test', level=Level.info)
        with self.assertSilent(), treelog.set(treelog.LoggingLog()), self.assertLogs('nutils'):
            recordlog.replay()


class SimplifiedRecordLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        recordlog = treelog.RecordLog(simplify=True)
        yield recordlog
        self.assertEqual(recordlog._messages, [
            ('write', 'my message', Level.user),
            ('write', Data('test.dat', b'test1'), Level.info),
            ('pushcontext', 'my context'),
            ('pushcontext', 'iter 1'),
            ('write', 'a', Level.info),
            ('recontext', 'iter 2'),
            ('write', 'b', Level.info),
            ('recontext', 'iter 3'),
            ('write', 'c', Level.info),
            ('popcontext',),
            ('write', 'multiple..\n  ..lines', Level.error),
            ('pushcontext', 'test.dat'),
            ('write', 'generating', Level.info),
            ('popcontext',),
            ('write', Data('test.dat', b'test2'), Level.user),
            ('recontext', 'generate_test'),
            ('write', Data('test.dat', b'test3'), Level.warning),
            ('recontext', 'context step=0'),
            ('write', 'foo', Level.info),
            ('recontext', 'context step=1'),
            ('write', 'bar', Level.info),
            ('popcontext',),
            ('write', Data('same.dat', b'test3'), Level.error),
            ('write', Data('dbg.dat', b'test4'), Level.debug),
            ('write', 'dbg', Level.debug),
            ('write', 'warn', Level.warning)])
        for Log in StdoutLog, DataLog, HtmlLog:
            with self.subTest('replay to {}'.format(Log.__name__)), Log.output_tester(self) as log:
                recordlog.replay(log)

    def test_replay_in_current(self):
        recordlog = treelog.RecordLog()
        recordlog.write('test', level=Level.info)
        with self.assertSilent(), treelog.set(treelog.LoggingLog()), self.assertLogs('nutils'):
            recordlog.replay()


class TeeLogTestLog:

    def __init__(self, dir, update, filenos):
        self._dir = dir
        self._update = update
        self.filenos = filenos

    def pushcontext(self, title):
        pass

    def popcontext(self):
        pass

    def recontext(self, title):
        pass

    def write(self, text, level):
        pass

    @contextlib.contextmanager
    def open(self, filename, mode, level):
        with open(os.path.join(self._dir, filename), mode+'+' if self._update else mode) as f:
            self.filenos.add(f.fileno())
            try:
                yield f
            finally:
                self.filenos.remove(f.fileno())


class TeeLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        with DataLog.output_tester(self) as datalog, \
                RecordLog.output_tester(self) as recordlog, \
                RichOutputLog.output_tester(self) as richoutputlog:
            yield treelog.TeeLog(richoutputlog, treelog.TeeLog(datalog, recordlog))

    def test_open_datalog_datalog_samedir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            teelog = treelog.TeeLog(treelog.DataLog(
                tmpdir), treelog.DataLog(tmpdir))
            teelog.write(Data('test', b'test'), Level.info)
            with open(os.path.join(tmpdir, 'test'), 'rb') as f:
                self.assertEqual(f.read(), b'test')
            with open(os.path.join(tmpdir, 'test-1'), 'rb') as f:
                self.assertEqual(f.read(), b'test')


class FilterMinLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        recordlog = treelog.RecordLog()
        yield treelog.FilterLog(recordlog, minlevel=Level.user)
        self.assertEqual(recordlog._messages, [
            ('write', 'my message', Level.user),
            ('pushcontext', 'my context'),
            ('write', 'multiple..\n  ..lines', Level.error),
            ('write', Data('test.dat', b'test2'), Level.user),
            ('recontext', 'generate_test'),
            ('write', Data('test.dat', b'test3'), Level.warning),
            ('popcontext',),
            ('write', Data('same.dat', b'test3'), Level.error),
            ('write', 'warn', Level.warning)])


class FilterMaxLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        recordlog = treelog.RecordLog()
        yield treelog.FilterLog(recordlog, maxlevel=Level.user)
        self.assertEqual(recordlog._messages, [
            ('write', 'my message', Level.user),
            ('write', Data('test.dat', b'test1'), Level.info),
            ('pushcontext', 'my context'),
            ('pushcontext', 'iter 1'),
            ('write', 'a', Level.info),
            ('recontext', 'iter 2'),
            ('write', 'b', Level.info),
            ('recontext', 'iter 3'),
            ('write', 'c', Level.info),
            ('recontext', 'test.dat'),
            ('write', 'generating', Level.info),
            ('popcontext',),
            ('write', Data('test.dat', b'test2'), Level.user),
            ('recontext', 'context step=0'),
            ('write', 'foo', Level.info),
            ('recontext', 'context step=1'),
            ('write', 'bar', Level.info),
            ('popcontext',),
            ('write', Data('dbg.dat', b'test4'), Level.debug),
            ('write', 'dbg', Level.debug)])


class FilterMinMaxLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        recordlog = treelog.RecordLog()
        yield treelog.FilterLog(recordlog, minlevel=Level.info, maxlevel=Level.warning)
        self.assertEqual(recordlog._messages, [
            ('write', 'my message', Level.user),
            ('write', Data('test.dat', b'test1'), Level.info),
            ('pushcontext', 'my context'),
            ('pushcontext', 'iter 1'),
            ('write', 'a', Level.info),
            ('recontext', 'iter 2'),
            ('write', 'b', Level.info),
            ('recontext', 'iter 3'),
            ('write', 'c', Level.info),
            ('recontext', 'test.dat'),
            ('write', 'generating', Level.info),
            ('popcontext',),
            ('write', Data('test.dat', b'test2'), Level.user),
            ('recontext', 'generate_test'),
            ('write', Data('test.dat', b'test3'), Level.warning),
            ('recontext', 'context step=0'),
            ('write', 'foo', Level.info),
            ('recontext', 'context step=1'),
            ('write', 'bar', Level.info),
            ('popcontext',),
            ('write', 'warn', Level.warning)])


class LoggingLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        with self.assertLogs('nutils') as cm:
            yield treelog.LoggingLog()
        self.assertEqual(cm.output, [
            'Level 25:nutils:my message',
            'INFO:nutils:test.dat',
            'INFO:nutils:my context > iter 1 > a',
            'INFO:nutils:my context > iter 2 > b',
            'INFO:nutils:my context > iter 3 > c',
            'ERROR:nutils:my context > multiple..\n  ..lines',
            'INFO:nutils:my context > test.dat > generating',
            'Level 25:nutils:my context > test.dat',
            'WARNING:nutils:generate_test > test.dat',
            'INFO:nutils:context step=0 > foo',
            'INFO:nutils:context step=1 > bar',
            'ERROR:nutils:same.dat',
            'WARNING:nutils:warn'])


class NullLog(Log):

    @contextlib.contextmanager
    def output_tester(self):
        with self.assertSilent():
            yield treelog.NullLog()

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
        self.assertEqual(self.recordlog._messages, list(msg))

    def test_context(self):
        with treelog.iter.plain('test', enumerate('abc')) as myiter:
            for i, c in myiter:
                self.assertEqual(c, 'abc'[i])
                treelog.info('hi')
        self.assertMessages(
            ('pushcontext', 'test 0'),
            ('recontext', 'test 1'),
            ('write', 'hi', Level.info),
            ('recontext', 'test 2'),
            ('write', 'hi', Level.info),
            ('recontext', 'test 3'),
            ('write', 'hi', Level.info),
            ('popcontext',))

    def test_nocontext(self):
        for i, c in treelog.iter.plain('test', enumerate('abc')):
            self.assertEqual(c, 'abc'[i])
            treelog.info('hi')
        self.assertMessages(
            ('pushcontext', 'test 0'),
            ('recontext', 'test 1'),
            ('write', 'hi', Level.info),
            ('recontext', 'test 2'),
            ('write', 'hi', Level.info),
            ('recontext', 'test 3'),
            ('write', 'hi', Level.info),
            ('popcontext',))

    def test_break_entered(self):
        with warnings.catch_warnings(record=True) as w, treelog.iter.plain('test', [1, 2, 3]) as myiter:
            for item in myiter:
                self.assertEqual(item, 1)
                treelog.info('hi')
                break
            gc.collect()
        self.assertEqual(w, [])
        self.assertMessages(
            ('pushcontext', 'test 0'),
            ('recontext', 'test 1'),
            ('write', 'hi', Level.info),
            ('popcontext',))

    def test_break_notentered(self):
        with self.assertWarns(ResourceWarning):
            for item in treelog.iter.plain('test', [1, 2, 3]):
                self.assertEqual(item, 1)
                treelog.info('hi')
                break
            gc.collect()
        self.assertMessages(
            ('pushcontext', 'test 0'),
            ('recontext', 'test 1'),
            ('write', 'hi', Level.info),
            ('popcontext',))

    def test_multiple(self):
        with treelog.iter.plain('test', 'abc', [1, 2]) as items:
            self.assertEqual(list(items), [('a', 1), ('b', 2)])

    def test_plain(self):
        with treelog.iter.plain('test', 'abc') as items:
            self.assertEqual(list(items), list('abc'))
        self.assertMessages(
            ('pushcontext', 'test 0'),
            ('recontext', 'test 1'),
            ('recontext', 'test 2'),
            ('recontext', 'test 3'),
            ('popcontext',))

    def test_plain_withbraces(self):
        with treelog.iter.plain('t{es}t', 'abc') as items:
            self.assertEqual(list(items), list('abc'))
        self.assertMessages(
            ('pushcontext', 't{es}t 0'),
            ('recontext', 't{es}t 1'),
            ('recontext', 't{es}t 2'),
            ('recontext', 't{es}t 3'),
            ('popcontext',))

    def test_fraction(self):
        with treelog.iter.fraction('test', 'abc') as items:
            self.assertEqual(list(items), list('abc'))
        self.assertMessages(
            ('pushcontext', 'test 0/3'),
            ('recontext', 'test 1/3'),
            ('recontext', 'test 2/3'),
            ('recontext', 'test 3/3'),
            ('popcontext',))

    def test_percentage(self):
        with treelog.iter.percentage('test', 'abc') as items:
            self.assertEqual(list(items), list('abc'))
        self.assertMessages(
            ('pushcontext', 'test 0%'),
            ('recontext', 'test 33%'),
            ('recontext', 'test 67%'),
            ('recontext', 'test 100%'),
            ('popcontext',))

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
            ('pushcontext', 'value'),
            ('recontext', "value='a'"),
            ('recontext', "value='b'"),
            ('recontext', "value='c'"),
            ('write', 'hi', Level.info),
            ('popcontext',))


class DocTest(unittest.TestCase):

    def test_docs(self):
        doctest.testmod(treelog)


del Log  # hide from unittest discovery

# INTERNALS


@contextlib.contextmanager
def capture():
    with tempfile.TemporaryFile('w+', newline='') as stdout, tempfile.TemporaryFile('w+', newline='') as stderr:
        class captured:
            pass
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            yield captured
        stdout.seek(0)
        captured.stdout = stdout.read()
        stderr.seek(0)
        captured.stderr = stderr.read()


@contextlib.contextmanager
def silent():
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
        yield

# vim:sw=2:sts=2:et
