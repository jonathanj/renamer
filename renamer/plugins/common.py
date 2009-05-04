import os, re, textwrap

from zope.interface import classProvides

from twisted.plugin import IPlugin

from renamer import logging
from renamer.irenamer import IRenamerPlugin
from renamer.plugin import Plugin, command
from renamer.util import Replacement, Replacer


class Common(Plugin):
    classProvides(IPlugin, IRenamerPlugin)

    name = None

    def __init__(self, **kw):
        super(Common, self).__init__(**kw)
        self.vars = {}

    @command
    def push(self, value):
        """
        Push an argument onto the stack.

        Parameters prefixed with a `$` are expanded from the variables
        dictionary (as stored by the `var` command.) `$$` produces a literal
        `$`.
        """
        if value.startswith('$'):
            if value.startswith('$$'):
                return value[1:]
            else:
                return self.vars[value[1:]]
        return value

    @command
    def pushdefault(self, value, default):
        """
        Push an argument onto the stack, optionally using a default.

        Primarily useful for when attempting to use `$` expansion might
        fail.
        """
        try:
            return self.push(value)
        except KeyError:
            return default

    @command
    def expanditer(self):
        """
        Pop and expand an iterable.

        An iterable is popped and each element pushed individually onto the
        stack. The value at the top of the stack is assumed to be iterable.

        e.g::
            rn> push "abc"
            rn> expanditer
            rn> stack
            --> 'a'
                'b'
                'c'
        """
        seq = list(iter(self.env.stack.pop()))
        for e in reversed(seq):
            self.env.stack.push(e)

    @command
    def pop(self):
        """
        Pop a value from the top of the stack.
        """
        self.env.stack.pop()

    @command
    def dup(self):
        """
        Duplicate the value at the top of the stack.
        """
        return self.env.stack.peek()

    @command
    def duplistn(self, seq, index):
        """
        Duplicate the value at a given index in a sequence.
        """
        index = int(index)
        self.env.stack.push(seq)
        return seq[index]

    @command
    def split(self, s, delim):
        """
        Split a string on a delimiter.
        """
        return s.split(delim)

    @command
    def splitn(self, s, delim, n):
        """
        Split a string on a delimiter up to `n` times.
        """
        return s.split(delim, int(n))

    @command
    def rsplitn(self, s, delim, n):
        """
        Split a string in reverse on a delimier up to `n` times.
        """
        return s.rsplit(delim, int(n))

    @command
    def join(self, it, delim):
        """
        Join an iterable with a delimiter.
        """
        return delim.join(it)

    @command
    def strip(self, s, chars):
        """
        Strip a string of characters.
        """
        return s.strip(chars)

    @command
    def title(self, s):
        """
        Title case a string.
        """
        return s.title()

    @command
    def lower(self, s):
        """
        Lower case a string.
        """
        return s.lower()

    @command
    def int(self, s):
        """
        Convert a string to an integer.
        """
        return int(s)

    @command
    def load(self, name):
        """
        Load a plugin by name.
        """
        self.env.load(name)

    @command
    def stack(self):
        """
        Pretty-print the current stack.
        """
        print self.env.stack.prettyFormat()

    @command
    def help(self, name):
        """
        Retrieve help for a given command.
        """
        cmd = self.env.resolveCommand(name)
        if cmd.__doc__:
            code = cmd.im_func.func_code
            argnames = code.co_varnames[1:code.co_argcount]
            doc = '%s(%s)\n%s' % (cmd.im_func.func_name,
                                  ', '.join(argnames),
                                  textwrap.dedent(cmd.__doc__.strip()))
        else:
            doc = 'No help available.'

        print doc
        print

    @command
    def inc(self, value):
        """
        Increment a numerical value.
        """
        return value + 1

    @command
    def dec(self, value):
        """
        Decrement a numerical value.
        """
        return value - 1

    # XXX: this sucks
    @command
    def camel_case_into_sentence(self, s):
        """
        Convert a camel-case string into a sentence.

        e.g::
            rn> push "LikeThisOne"
            rn> camel_case_into_sentence
            rn> stack
            --> 'Like This One'
        """
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
        """
        Store a variable.
        """
        self._setvar(name, value)

    @command
    def envvar(self, name, default):
        """
        Get an environment variable.
        """
        return os.environ.get(name, default)

    @command
    def format(self, fmt):
        """
        Perform string interpolation with the stored variable dictionary.
        """
        return fmt % self.vars

    @command
    def quit(self):
        """
        Exit the environment.
        """
        raise EOFError()


class OS(Plugin):
    classProvides(IPlugin, IRenamerPlugin)

    name = 'os'

    def __init__(self, **kw):
        super(OS, self).__init__(**kw)
        self.repl = Replacement.fromIterable(self.openFile('replace'))
        self.repl.add(Replacer(r'[*<>/]', ''))

    @command
    def move(self, src, dstDir):
        """
        Move a file to a directory.
        """
        dstPath = os.path.join(dstDir, src)
        if self.env.isMoveEnabled:
            logging.msg('Move: %s ->\n %s' % (src, dstPath))
            if not self.env.isDryRun:
                if not os.path.exists(dstDir):
                    os.makedirs(dstDir)
                os.rename(src, dstPath)

        return dstPath

    @command
    def rename(self, src, dst):
        """
        Rename a file.
        """
        dst = self.repl.replace(dst)

        logging.msg('Rename: %s ->\n  %s' % (src, dst))
        if not self.env.isDryRun:
            os.rename(src, dst)

        return dst
