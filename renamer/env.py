import codecs, os, shlex

from twisted.internet.defer import maybeDeferred, succeed
from twisted.python.filepath import FilePath

import renamer
from renamer import logging
from renamer.errors import PluginError, StackError, EnvironmentError
from renamer.plugin import getGlobalPlugins, getPlugin


class EnvironmentMode(object):
    """
    Environment mode settings.

    @type dryrun: C{bool}
    @ivar dryrun: Perform a dry run, meaning that no changes, such as file 
        renames, are persisted

    @type move: C{bool}
    @ivar move: Enable file moving
    """
    def __init__(self, dryrun, move):
        self.dryrun = dryrun
        self.move = move


class Environment(object):
    """
    Renamer script environment.

    @type mode: L{EnvironmentMode}

    @type verbosity: C{int}
    @ivar verbosity: Verbosity level::

        0 - Quiet

        1 - Normal

        2 - Verbose

    @type stack: L{Stack}

    @type _plugins: C{dict} mapping C{str} to C{dict} mapping C{str} to C{callable}
    @ivar _plugins: Mapping of C{pluginName} to a mapping of C{commandName} to commands
    """
    def __init__(self, args, mode, verbosity):
        self.mode = mode
        self.verbosity = verbosity

        self.stack = Stack()
        self._plugins = {}

        if self.isDryRun:
            logging.msg('Performing a dry-run.', verbosity=2)

        if self.isMoveEnabled:
            logging.msg('Moving is enabled.', verbosity=2)

        for p in getGlobalPlugins():
            self._loadPlugin(p)

        for arg in args:
            self.stack.push(arg)

    @property
    def isDryRun(self):
        return self.mode.dryrun

    @property
    def isMoveEnabled(self):
        return self.mode.move

    def openPluginFile(self, plugin, filename):
        """
        Open a user-provided file for a plugin.

        @rtype: C{file} or C{None}
        @return: File object or C{None} if no such file exists, or C{plugin}
            is a global plugin
        """
        if plugin.name is not None:
            path = FilePath(os.path.expanduser('~/.renamer')).child(plugin.name).child(filename)
            if path.exists():
                return path.open()
        return None

    def getScriptPaths(self):
        """
        Retrieve valid script directories.

        @rtype: C{iterable} of C{FilePath} instances
        """
        path = FilePath(os.path.expanduser('~/.renamer/scripts'))
        if path.exists():
            yield path

        path = FilePath(renamer.__file__).parent().sibling('scripts')
        if path.exists():
            yield path

    def openScript(self, filename):
        """
        Attempt to open a script file.

        The filename is tried as is, in the context of the current working
        path, and then the global script paths are tried.

        @raise EnvironmentError: If C{filename} cannot be found

        @rtype: C{file}
        """
        def _found(path):
            logging.msg('Found script: %r.' % (path,), verbosity=2)
            return codecs.open(path.path, 'rb')

        def _getPaths():
            yield FilePath(filename)
            for path in self.getScriptPaths():
                yield path.child(filename)

        for path in _getPaths():
            if path.exists():
                return _found(path)

        raise EnvironmentError('No script named %r.' % (filename,))

    def runScript(self, filename):
        """
        Execute a script file.
        """
        fd = self.openScript(filename)

        logging.msg('Running script...', verbosity=2)

        def _runLine(result, line):
            def maybeVerbose(result):
                if self.verbosity > 2:
                    logging.msg('rn> ' + line)
                    return self.execute('stack')
            return self.execute(line).addCallback(maybeVerbose)

        d = succeed(None)
        for line in fd:
            if not line.strip() or line.startswith(u'#'):
                continue
            d.addCallback(_runLine, line)

        return d

    def _getCommands(self, plugin):
        """
        Enumerate plugin commands.
        """
        for name in dir(plugin):
            attr = getattr(plugin, name, None)
            if getattr(attr, 'command', False):
                yield name, attr

    def _loadPlugin(self, pluginType):
        """
        Create an instance of C{pluginType} and map its commands.
        """
        p = pluginType(env=self)
        pluginName = p.name or None

        commands = self._plugins.setdefault(pluginName, {})
        for name, cmd in self._getCommands(p):
            commands[name] = cmd

    def load(self, pluginName):
        """
        Load a plugin by name.
        """
        self._loadPlugin(getPlugin(pluginName))

    def _resolveCommand(self, pluginName, name):
        """
        Resolve a plugin command by name.
        """
        commands = self._plugins.get(pluginName)
        if commands is None:
            raise PluginError('No plugin named %r.' % (pluginName,))

        cmd = commands.get(name)
        if cmd is None:
            raise PluginError('No command named %r.' % (name,))

        return cmd

    def resolveCommand(self, name):
        """
        Resolve a command by name.
        """
        if '.' in name:
            pluginName, name = name.split('.', 1)
        else:
            pluginName = None
        return self._resolveCommand(pluginName, name)

    def parse(self, line):
        """
        Parse input according to shell-like rules.

        @rtype: C{(callable, list)}
        @return: A 2-tuple containing a command callable and a sequence of
            arguments
        """
        args = shlex.split(line)
        name = args.pop(0)
        return self.resolveCommand(name), args

    def execute(self, line):
        """
        Execute a line of input.

        @rtype: C{Deferred}
        """
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
