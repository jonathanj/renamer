import os, re, sys

from zope.interface import classProvides

from twisted.plugin import IPlugin

from renamer.irenamer import IRenamerPlugin
from renamer.plugin import command


class Common(object):
    classProvides(IPlugin, IRenamerPlugin)

    name = None

    def __init__(self, env):
        super(Common, self).__init__()
        self.env = env
        self.vars = {}

    @command
    def push(self, value):
        if value.startswith('$'):
            if value.startswith('$$'):
                return value[1:]
            else:
                return self.vars[value[1:]]
        return value

    @command
    def pushdefault(self, value, default):
        try:
            return self.push(value)
        except KeyError:
            return default

    @command
    def pushlist(self):
        l = self.env.stack.pop()
        for e in reversed(l):
            self.env.stack.push(e)

    @command
    def pop(self, dummy):
        return None

    @command
    def dup(self):
        return self.env.stack.peek()

    @command
    def duplistn(self, l, index):
        index = int(index)
        self.env.stack.push(l)
        return l[index]

    @command
    def split(self, s, delim):
        return s.split(delim)

    @command
    def splitn(self, s, delim, n):
        return s.split(delim, int(n))

    @command
    def rsplitn(self, s, delim, n):
        return s.rsplit(delim, int(n))

    @command
    def join(self, l, delim):
        return delim.join(l)

    @command
    def strip(self, s, c):
        return s.strip(c)

    @command
    def title(self, s):
        return s.title()

    @command
    def lower(self, s):
        return s.lower()

    @command
    def int(self, s):
        return int(s)

    @command
    def load(self, name):
        self.env.load(name)

    @command
    def stack(self):
        print self.env.stack.prettyPrint()

    @command
    def help(self, name):
        cmd = self.env.resolveCommand(name)
        if cmd.__doc__:
            print cmd.__doc__
        else:
            print 'No help available.'

    @command
    def inc(self, value):
        return value + 1

    @command
    def dec(self, value):
        return value - 1

    # XXX: this sucks
    @command
    def camel_case_into_sentence(self, s):
        """Converts a proper camel-case string (LikeThisOne) into a sentence (Like This One)."""
        return re.sub(r'(?<![\s-])([A-Z\(])', r' \1', s).strip()

    def _setvar(self, name, value):
        self.vars[name] = value

    @command
    def regex(self, s, r):
        m = re.match(r, s)
        if m is not None:
            for key, value in m.groupdict().iteritems():
                self._setvar(key, value)
            return list(m.groups())

    @command
    def var(self, value, name):
        self._setvar(name, value)

    @command
    def envvar(self, varname):
        return os.environ[varname]

    @command
    def format(self, fmt):
        return fmt % self.vars


class OS(object):
    classProvides(IPlugin, IRenamerPlugin)

    name = 'os'

    def __init__(self, env):
        super(OS, self).__init__()
        self.env = env

        self.replacements = list(self._makeFilenameReplacements())

    def _makeFilenameReplacements(self):
        # XXX: should we be hardcoding this?
        yield re.compile(r'[*<>]'), ''

        fd = self.env.openUserFile('replace')
        if fd is not None:
            for line in fd:
                line = line.strip()
                if line:
                    regex, repl = line.split('\t', 1)
                    yield re.compile(regex), repl

    def _makeSaneFilename(self, fn):
        for r, repl in self.replacements:
            fn = r.sub(repl, fn)
        return fn

    @command
    def move(self, src, dstDir):
        dstPath = os.path.join(dstDir, src)
        if self.env.movemode:
            print 'Move: %s ->\n %s' % (src, dstPath)
            if not self.env.safemode:
                if not os.path.exists(dstDir):
                    os.makedirs(dstDir)
                os.rename(src, dstPath)

        return dstPath

    @command
    def rename(self, src, dst):
        dst = self._makeSaneFilename(dst)

        print 'Rename: %s ->\n  %s' % (src, dst)
        if not self.env.safemode:
            os.rename(src, dst)

        return dst
