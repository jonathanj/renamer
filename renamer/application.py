"""
Renamer application logic.
"""
import glob, os, stat, sys, time

from twisted.internet import reactor
from twisted.internet.defer import DeferredSemaphore, succeed
from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver
from twisted.python import log, usage
from twisted.python.versions import getVersionString

from renamer import version
from renamer.env import Environment, EnvironmentMode
from renamer.util import parallel


class ArgumentSorter(object):
    """
    Sort arguments according to a certain method.
    """

    @staticmethod
    def byMtime(path):
        """
        Sort according to modification time.
        """
        try:
            return time.localtime(os.stat(path)[stat.ST_MTIME])
        except OSError:
            return -1

    @staticmethod
    def bySize(path):
        """
        Sort according to file size.
        """
        try:
            return os.stat(path)[stat.ST_SIZE]
        except OSError:
            return -1

    @staticmethod
    def byName(path):
        """
        Sort according to file name.
        """
        return path

    @staticmethod
    def sort(names, method):
        """
        Sort names according to a given method.

        @type names: C{list}

        @type method: C{str}
        """
        names.sort(key=self._sortMethods[method])

    _sortMethods = {
        'time': byMtime,
        'size': bySize,
        'name': byName}


class Options(usage.Options):
    """
    Renamer command-line arguments.
    """
    synopsis = '[options] target [target ...]'

    optFlags = [
        ['glob',    'g', 'Expand filenames as UNIX-style globs'],
        ['move',    'm', 'Move files'],
        ['reverse', 'R', 'Reverse sorting order'],
        ['dry-run', 't', 'Perform a dry-run'],
        ]

    optParameters = [
        ['script',  's', None,   'Renamer script to execute'],
        ['sort',    'S', 'name', 'Sort filenames by criteria: created, name, size']
        ]

    def __init__(self):
        usage.Options.__init__(self)
        self['verbosity'] = 1

    def opt_verbose(self):
        """
        Increase output
        """
        self['verbosity'] = self['verbosity'] + 1

    opt_v = opt_verbose

    def opt_quiet(self):
        """
        Suppress output
        """
        self['verbosity'] = self['verbosity'] - 1

    opt_q = opt_quiet

    def sortArguments(self, targets):
        """
        Sort arguments according to options.
        """
        if self['sort']:
            ArgumentSorter.sort(targets, self['sort'])
        if self['reverse']:
            targets.reverse()
        return targets

    def glob(self, targets):
        """
        Glob arguments.
        """
        def _glob():
            return [target for _target in targets
                           for target in glob.glob(_target)]

        def _globWin32():
            _targets = []
            for target in targets:
                if not os.path.exists(target):
                    globbed = glob.glob(target)
                    if globbed:
                        _targets.extend(globbed)
                        continue

                _targets.append(target)
            return _targets

        if sys.platform == 'win32':
            return _globWin32()
        return _glob()

    def parseArgs(self, *targets):
        """
        Parse command-line arguments.
        """
        if self['script'] and len(targets) == 0:
            raise usage.UsageError('Too few arguments')

        if self['glob']:
            targets = self.glob(targets)
        self.targets = self.sortArguments(list(targets))


class Renamer(object):
    def __init__(self, options, maxConcurrentScripts=10):
        """
        Initialise a Renamer.

        @type options: L{Options}
        @param options: Parsed command-line options

        @type maxConcurrentScripts: C{int}
        @param maxConcurrentScripts: Maximum number of scripts to execute in
            parallel, defaults to 10
        """
        self.options = options
        self.maxConcurrentScripts = maxConcurrentScripts
        self.targets = options.targets

    def createEnvironment(self, args):
        """
        Create a new environment.

        @type args: C{iterable}
        @param args: Initial stack arguments
        """
        mode = EnvironmentMode(dryrun=self.options['dry-run'],
                               move=self.options['move'])
        return Environment(args,
                           mode=mode,
                           verbosity=self.options['verbosity'])

    def run(self):
        """
        Start running.

        If the script option was used, the script is run for all command-line
        arguments, and afterwards execution will stop. Otherwise interactive
        mode is initiated.
        """
        if self.options['script']:
            self.runScript(self.options['script']
                ).addErrback(log.err
                ).addCallback(lambda result: reactor.stop())
        else:
            self.runInteractive()

    def runScript(self, script):
        """
        Run the given script in the environent.

        The script is executed for each command-line argument, in parallel, up
        to a maximum of L{maxConcurrentScripts}.
        """
        def _runScript(target):
            env = self.createEnvironment([target])
            return env.runScript(script)

        return parallel(self.targets, self.MAX_CONCURRENT_SCRIPTS, _runScript)

    def runInteractive(self):
        """
        Begin interactive mode.

        Interactive mode is ended with an EOF.
        """
        env = self.createEnvironment(self.targets)
        StandardIO(RenamerInteractive(env))


class RenamerInteractive(LineReceiver):
    """
    Interactive Renamer session.

    @type semaphore: C{twisted.internet.defer.DeferredSemaphore}
    @ivar semaphore: Semaphore for serializing command execution
    """
    delimiter = os.linesep

    def __init__(self, env):
        """
        Initialise an interactive Renamer environment.

        @type env: L{Environment}
        @param env: Renamer environment for the interactive session
        """
        self.env = env
        self.semaphore = DeferredSemaphore(tokens=1)

    def heading(self):
        """
        Display application header.
        """
        self.transport.write(getVersionString(version) + self.delimiter)

    def prompt(self):
        """
        Display application prompt.
        """
        self.transport.write('rn> ')

    def connectionMade(self):
        self.heading()
        self.prompt()

    def connectionLost(self, reason):
        reactor.stop()

    def lineReceived(self, line):
        def _doLine(result):
            return self.env.execute(line)

        d = succeed(None)

        line = line.strip()
        if line:
            d = self.semaphore.acquire(
                ).addCallback(_doLine
                ).addErrback(log.err
                ).addBoth(lambda result: self.semaphore.release())

        d.addCallback(lambda result: self.prompt())
