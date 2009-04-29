import codecs, os, shlex

from twisted.internet.defer import maybeDeferred, succeed
from twisted.python.filepath import FilePath

import renamer
from renamer import logging
from renamer.errors import PluginError, StackError, EnvironmentError
from renamer.plugin import getGlobalPlugins, getPlugin


class Environment(object):
    def __init__(self, args, safemode, movemode, verbosity):
        self.safemode = safemode
        self.movemode = movemode
        self.verbosity = verbosity

        self.stack = Stack()
        self.plugins = {}
        self.globals = []

        if self.safemode:
            logging.msg('Safemode enabled.', verbosity=2)

        for p in getGlobalPlugins():
            self._loadPlugin(p)

        for arg in args:
            self.stack.push(arg)

    def openPluginFile(self, plugin, filename):
        if plugin.name is not None:
            path = FilePath(os.path.expanduser('~/.renamer')).child(plugin.name).child(filename)
            if path.exists():
                return path.open()
        return None

    def getScriptPaths(self):
        path = FilePath(os.path.expanduser('~/.renamer/scripts'))
        if path.exists():
            yield path

        path = FilePath(renamer.__file__).parent().sibling('scripts')
        if path.exists():
            yield path

    def openScript(self, filename):
        for path in self.getScriptPaths():
            path = path.child(filename)
            if path.exists():
                logging.msg('Found script: %r.' % (path,), verbosity=2)
                return codecs.open(path.path, 'rb')

        raise EnvironmentError('No script named %r.' % (filename,))

    def runScript(self, filename):
        fd = self.openScript(filename)

        logging.msg('Running script...', verbosity=2)

        def _runLine(result, line):
            def maybeVerbose(result):
                if self.verbosity > 2:
                    print 'rn>', line
                    # XXX:
                    return self.execute('stack')
            return self.execute(line).addCallback(maybeVerbose)

        d = succeed(None)
        for line in fd:
            if not line.strip() or line.startswith(u'#'):
                continue
            d.addCallback(_runLine, line)

        return d

    def _loadPlugin(self, pluginType):
        p = pluginType(env=self)
        if p.name is None:
            self.globals.append(p)
        else:
            self.plugins[p.name] = p

    def load(self, pluginName):
        if pluginName in self.plugins:
            return
        self._loadPlugin(getPlugin(pluginName))

    def _resolveGlobalCommand(self, name):
        for p in self.globals:
            cmd = getattr(p, name, None)
            if cmd is not None:
                return cmd

        raise PluginError('No global command named %r.' % (name,))

    def _resolveCommand(self, pluginName, name):
        try:
            p = self.plugins[pluginName]
            cmd = getattr(p, name, None)
            if cmd is None:
                raise PluginError('No command named %r in plugin %r.' % (name, pluginName))
            return cmd
        except KeyError:
            raise PluginError('No plugin named %r.' % (pluginName,))

    def resolveCommand(self, name):
        if '.' in name:
            pluginName, name = name.split('.', 1)
            cmd = self._resolveCommand(pluginName, name)
        else:
            cmd = self._resolveGlobalCommand(name)

        if getattr(cmd, 'command', False):
            return cmd

        raise PluginError('Not a command %r.' % (name,))

    def parse(self, line):
        args = shlex.split(line)
        name = args.pop(0)
        return self.resolveCommand(name), args

    def execute(self, line):
        def _execute():
            fn, args = self.parse(line)
            n = fn.func_code.co_argcount - 1

            def _normalizeArgs():
                numArgsOnStack = n - len(args) - 1
                return self.stack.popArgs(numArgsOnStack) + args

            args = _normalizeArgs()

            for arg in args:
                self.stack.push(arg)

            self.stack.push(fn)
            return self.stack.call(n)

        return maybeDeferred(_execute)


class Stack(object):
    def __init__(self):
        self.stack = []

    def size(self):
        return len(self.stack)

    def push(self, value):
        """
        Push a value on to the top of the stack.
        """
        self.stack.insert(0, value)

    def pop(self):
        """
        Retrieve the value from the top of the stack.
        """
        if self.size() == 0:
            raise StackError('Popping from an empty stack')
        return self.stack.pop(0)

    def peek(self):
        """
        Retrieve the value from the top of the stack, non-destructively.
        """
        return self.stack[0]

    def popArgs(self, numArgs):
        if self.size() < numArgs:
            raise StackError('Expecting %d stack arguments but only found %d' % (numArgs, self.size()))
        return list(reversed([self.pop() for _ in xrange(numArgs)]))

    def call(self, numArgs):
        """
        Call the function at the top of the stack.

        The top and C{numArgs} entries are popped from the stack, with the
        return value from the function being left on top of the stack.
        """
        fn = self.pop()

        if numArgs:
            args = self.popArgs(numArgs)
        else:
            args = []

        def pushResult(rv):
            if rv is not None:
                self.push(rv)

        return maybeDeferred(fn, *args
            ).addCallback(pushResult)

    def prettyFormat(self):
        """
        Get a human-readable stack visualisation.

        @rtype: C{unicode}
        """
        if not self.stack:
            return '<Empty stack>'

        s = u'-->'
        for v in self.stack:
            s += u' %r\n' % (v,)
            s += '   '

        return s.rstrip(u' ')

    def __repr__(self):
        return '<%s size=%d>' % (
            type(self).__name__,
            self.size())
