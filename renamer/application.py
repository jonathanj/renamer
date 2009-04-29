import glob, os, stat, sys, time

from twisted.internet import reactor
from twisted.internet.defer import DeferredSemaphore
from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver
from twisted.python import log, usage
from twisted.python.versions import getVersionString

from renamer import version
from renamer.env import Environment
from renamer.util import parallel


def sortByCtime(path):
    try:
        return time.localtime(os.stat(path)[stat.ST_CTIME])
    except OSError:
        return -1


def sortBySize(path):
    try:
        return os.stat(path)[stat.ST_SIZE]
    except OSError:
        return -1


def sortByName(path):
    return path


class Options(usage.Options):
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

    _sortMethods = {
        'created': sortByCtime,
        'size':    sortBySize,
        'name':    sortByName}

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
        if self['sort']:
            targets.sort(key=self._sortMethods[self['sort']])
        if self['reverse']:
            targets.reverse()
        return targets

    def glob(self, targets):
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
        if self['script'] and len(targets) == 0:
            raise usage.UsageError('Too few arguments')

        if self['glob']:
            targets = self.glob(targets)
        self.targets = self.sortArguments(list(targets))


class Renamer(object):
    MAX_CONCURRENT_SCRIPTS = 10

    def __init__(self, options):
        self.options = options
        self.targets = options.targets

    def createEnvironment(self, targets):
        return Environment(targets,
                           safemode=self.options['dry-run'],
                           movemode=self.options['move'],
                           verbosity=self.options['verbosity'])

    def run(self):
        if self.options['script']:
            self.runScript(self.options['script']
                ).addErrback(log.err
                ).addCallback(lambda result: reactor.stop())
        else:
            self.runInteractive()

    def runScript(self, script):
        def _runScript(target):
            env = self.createEnvironment([target])
            return env.runScript(script)

        return parallel(self.targets, self.MAX_CONCURRENT_SCRIPTS, _runScript)

    def runInteractive(self):
        env = self.createEnvironment(self.targets)
        StandardIO(RenamerInteractive(env))


class RenamerInteractive(LineReceiver):
    delimiter = os.linesep

    def __init__(self, env):
        self.env = env
        self.semaphore = DeferredSemaphore(tokens=1)

    def heading(self):
        self.transport.write(getVersionString(version) + self.delimiter)

    def prompt(self):
        self.transport.write('rn> ')

    def connectionMade(self):
        self.heading()
        self.prompt()

    def connectionLost(self, reason):
        reactor.stop()

    def lineReceived(self, line):
        def _doLine(result):
            return self.env.execute(line)

        line = line.strip()
        if line:
            self.semaphore.acquire(
                ).addCallback(_doLine
                ).addErrback(log.err
                ).addBoth(lambda result: self.semaphore.release()
                ).addCallback(lambda result: self.prompt())
