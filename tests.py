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
        self.assertEqual(f.getvalue(),
            '\x1b[1;34mmy message\x1b[0m\n'
            'test.dat > '
            '\r\x1b[K'
            '\x1b[1mtest.dat [5 bytes]\x1b[0m\n'
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
            '\x1b[1;34mtest.dat [5 bytes]\x1b[0m\nmy context > '
            '\r\x1b[Kgenerate_test > test.dat > '
            '\x1b[11D\x1b[K'
            '\x1b[1;35mtest.dat [5 bytes]\x1b[0m\ngenerate_test > '
            '\r\x1b[K'
            'context step=0 > '
            '\x1b[1mfoo\x1b[0m\n'
            'context step=0 > '
            '\x1b[4D1 > '
            '\x1b[1mbar\x1b[0m\n'
            'context step=1 > '
            '\r\x1b[K'
            '\x1b[1;31msame.dat [5 bytes]\x1b[0m\n'
            'dbg.jpg > '
            '\r\x1b[K'
            '\x1b[1;30mdbg.jpg [image/jpg; 5 bytes]\x1b[0m\n'
            '\x1b[1;30mdbg\x1b[0m\n'
            '\x1b[1;35mwarn\x1b[0m\n')


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
        tests = ['b444ac06613fc8d63795be9ad0beaf55011936ac.dat', '109f4b3c50d7b0df729d299bc6f8e9ef9066971f.dat',
                 '3ebfa301dc59196f18593c45e519287a23297589.dat', '1ff2b3704aede04eecb51e50ca698efd50a1379b.jpg']
        self.assertEqual(filename, 'log.html')
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
            '<div class="item" data-loglevel="0"><a href="1ff2b3704aede04eecb51e50ca698efd50a1379b.jpg" download="dbg.jpg">dbg.jpg</a></div>\n',
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
            with treelog.HtmlLog(outdira) as log:
                os.rename(outdira, outdirb)
                os.mkdir(outdira)
                log.write(Data('dat', b''), Level.info)
            self.assertIn(
                'da39a3ee5e6b4b0d3255bfef95601890afd80709', os.listdir(outdirb))

    def test_filename_sequence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with treelog.HtmlLog(tmpdir) as log:
                pass
            self.assertTrue(os.path.exists(os.path.join(tmpdir, 'log.html')))
            with treelog.HtmlLog(tmpdir) as log:
                pass
            self.assertTrue(os.path.exists(os.path.join(tmpdir, 'log-1.html')))
            with treelog.HtmlLog(tmpdir) as log:
                pass
            self.assertTrue(os.path.exists(os.path.join(tmpdir, 'log-2.html')))


class RecordLog(unittest.TestCase):

    simplify = False

    def test_output(self):
        recordlog = treelog.RecordLog(simplify=self.simplify)
        with treelog.set(recordlog):
            generate()
        self.check_output(recordlog._messages)
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
        if not self.simplify:
            with self.subTest('replay to RichOutputLog'):
                f = io.StringIO()
                recordlog.replay(treelog.RichOutputLog(f))
                RichOutputLog.check_output(self, f)

    def check_output(self, messages):
        self.assertEqual(messages, [
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
            ('write', Data('same.dat', b'test3'), Level.error),
            ('pushcontext', 'dbg.jpg'),
            ('popcontext',),
            ('write', Data('dbg.jpg', b'test4', type='image/jpg'), Level.debug),
            ('write', 'dbg', Level.debug),
            ('write', 'warn', Level.warning)])

    def test_replay_in_current(self):
        recordlog = treelog.RecordLog(simplify=self.simplify)
        recordlog.write('test', level=Level.info)
        with treelog.set(treelog.LoggingLog()), self.assertLogs('nutils'):
            recordlog.replay()


class SimplifiedRecordLog(RecordLog):

    simplify = True

    def check_output(self, messages):
        self.assertEqual(messages, [
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
            ('write', Data('dbg.jpg', b'test4', type='image/jpg'), Level.debug),
            ('write', 'dbg', Level.debug),
            ('write', 'warn', Level.warning)])


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
                RecordLog.check_output(self, recordlog._messages)
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
        self.check_output(recordlog._messages)

    def check_output(self, messages):
        self.assertEqual(messages, [
            ('write', 'my message', Level.user),
            ('pushcontext', 'my context'),
            ('write', 'multiple..\n  ..lines', Level.error),
            ('write', Data('test.dat', b'test2'), Level.user),
            ('recontext', 'generate_test'),
            ('write', Data('test.dat', b'test3'), Level.warning),
            ('popcontext',),
            ('write', Data('same.dat', b'test3'), Level.error),
            ('write', 'warn', Level.warning)])


class FilterMaxLog(unittest.TestCase):

    def test_output(self):
        recordlog = treelog.RecordLog()
        with treelog.set(treelog.FilterLog(recordlog, maxlevel=Level.user)):
            generate()
        self.check_output(recordlog._messages)

    def check_output(self, messages):
        self.assertEqual(messages, [
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
            ('write', Data('dbg.jpg', b'test4', type='image/jpg'), Level.debug),
            ('write', 'dbg', Level.debug)])


class FilterMinMaxLog(unittest.TestCase):

    def test_output(self):
        recordlog = treelog.RecordLog()
        with treelog.set(treelog.FilterLog(recordlog, minlevel=Level.info, maxlevel=Level.warning)):
            generate()
        self.check_output(recordlog._messages)

    def check_output(self, messages):
        self.assertEqual(messages, [
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
