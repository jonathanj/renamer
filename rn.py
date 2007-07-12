import os
import sys
import glob
import shlex
import logging
import optparse

from renamer.plugins import PluginError

class StackError(Exception): pass

class Stack(object):
    def __init__(self):
        self.stack = []

    def push(self, value):
        self.stack.insert(0, value)

    def pop(self):
        return self.stack.pop(0)

    def peek(self):
        return self.stack[0]

    def popArgs(self, n):
        if len(self.stack) < n:
            raise StackError('Expecting %d stack arguments but only found %d' % (n, len(self.stack)))
        return list(reversed([self.pop() for _ in xrange(n)]))

    def call(self, n):
        fn = self.pop()

        if n:
            args = self.popArgs(n)
        else:
            args = []

        rv = fn(*args)
        if rv is not None:
            self.push(rv)

    def __repr__(self):
        if not self.stack:
            return '<Empty stack>'

        s = ''
        for n in xrange(len(self.stack)):
            if n == 0:
                s += '-->'
            else:
                s += '   '
            s += ' ' + repr(self.stack[n]) + '\n'

        return s


class Environment(object):
    AUTO_LOAD = ['common']

    def __init__(self, args, safemode, verbosity):
        self.stack = Stack()
        self.plugins = {}
        self.globals = []
        self.verbosity = verbosity
        self.safemode = safemode

        if self.safemode:
            logging.info('Safemode enabled.')

        self.appPath = os.path.split(__import__('renamer').__file__)[0]
        self.scriptPath = os.path.join(self.appPath, 'scripts')

        for pluginName in self.AUTO_LOAD:
            self.load(pluginName, globalNamespace=True)

        for arg in args:
            self.stack.push(arg)

    def runScript(self, filename):
        try:
            fd = file(filename, 'rb')
        except IOError:
            logging.info('%r not found, trying global scripts...' % (filename,))
            filename = os.path.join(self.scriptPath, filename)
            if not os.path.exists(filename):
                raise
            fd = file(filename, 'rb')

        logging.info('Running script %r...' % (filename,))
        for line in file(filename):
            if not line.strip() or line.startswith('#'):
                continue

            self.execute(line)
            if self.verbosity >= 2:
                print 'rn>', line
                # XXX:
                self.execute('stack')

    def load(self, pluginName, globalNamespace=False):
        if pluginName in self.plugins:
            return

        try:
            mod = __import__('renamer.plugins.' + pluginName, globals(), locals(), [pluginName])
        except ImportError, e:
            raise PluginError('Unable to load plugin %r: %s' % (pluginName, e))

        commands = {}
        for key, value in vars(mod).iteritems():
            if hasattr(value, 'pluginCommand') and value.pluginCommand:
                commands[key] = value

        self.plugins[pluginName] = commands

        if globalNamespace:
            self.globals.append(pluginName)
            logging.info('Added %r plugin to the global namespace.' % (pluginName,))

        logging.info('%d commands were loaded from the %r plugin.' % (len(commands), pluginName))

    def resolveFunction(self, cmd):
        if '.' in cmd:
            pn, cmd = cmd.split('.', 1)
        else:
            for pluginName in self.globals:
                if cmd in self.plugins[pluginName]:
                    pn = pluginName
                    break
            else:
                raise PluginError('No such command %r.' % (cmd,))

        try:
            plugin = self.plugins[pn]
        except KeyError:
            raise PluginError('No such plugin named %r.' % (pn,))

        try:
            fn = plugin[cmd]
        except KeyError:
            raise PluginError('No such command %r in plugin %r.' % (cmd, pn))

        return fn

    def parse(self, line):
        args = shlex.split(line)
        cmd = args.pop(0)

        return self.resolveFunction(cmd), args

    def execute(self, line):
        try:
            fn, args = self.parse(line)
        except PluginError, e:
            logging.error('Error parsing input: %s' % (e,))
            return

        n = fn.func_code.co_argcount

        def _normalizeArgs():
            numArgsOnStack = n - len(args) - 1
            return self.stack.popArgs(numArgsOnStack) + args

        args = _normalizeArgs()

        self.stack.push(self)
        for arg in args:
            self.stack.push(arg)

        self.stack.push(fn)
        try:
            self.stack.call(n)
        except StackError, e:
            logging.error('Error calling function: %s' % (e,))
            return

def main():
    parser = optparse.OptionParser(usage='%prog [options] script_file file1 [file2 ...]')
    parser.add_option('-t', '--dry-run', dest='dryrun', action='store_true', help='Perform a dry-run')
    parser.add_option('-s', '--script', dest='script', action='store', help='Command script to execute')
    parser.add_option('-v', action='count', dest='verbosity', default=0, help='Increase output verbosity')
    parser.add_option('-g', '--glob', dest='glob', action='store_true', help='Expand filenames as UNIX-style globs')
    options, args = parser.parse_args()

    if options.script and len(args) < 1:
        parser.error('too few arguments')

    verbosity = options.verbosity

    if verbosity == 0:
        logging.basicConfig(level=logging.WARNING)
    elif verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    def expandArgs():
        return args

    def expandArgsWin32():
        _args = []
        for arg in args:
            if not os.path.exists(arg):
                globbed = glob.glob(arg)
                if globbed:
                    _args.extend(globbed)
                    continue

            _args.append(arg)
        return _args

    def expandArgsGlob():
        _args = []
        for arg in args:
            _args.extend(glob.glob(arg))
        return _args

    if options.glob:
        targets = expandArgsGlob()
    elif sys.platform == 'win32':
        targets = expandArgsWin32()
    else:
        targets = expandArgs()

    env = Environment(targets, safemode=options.dryrun, verbosity=verbosity)
    if options.script is not None:
        # Run the script as many times as there are targets
        # XXX: this is a bit of hack
        for _ in targets:
            env.runScript(options.script)
    else:
        try:
            while True:
                env.execute(raw_input('rn> '))
        except EOFError:
            print

if __name__ == '__main__':
    main()
