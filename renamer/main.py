import glob, logging, optparse, os, sys, stat, time

from twisted.internet import reactor
from twisted.internet.defer import DeferredSemaphore
from twisted.internet.stdio import StandardIO
from twisted.protocols.basic import LineReceiver
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


class Renamer(object):
    _sortMethods = {
        'created': sortByCtime,
        'size':    sortBySize,
        'name':    sortByName}

    MAX_SIMULTANEOUS_SCRIPTS = 10

    def __init__(self):
        self.options, self.targets = self.parseOptions()

        self.setupLogging()

        if self.options.sort:
            self.targets.sort(key=self._sortMethods[self.options.sort])
        if self.options.reverse:
            self.targets.reverse()

    def createEnvironment(self, targets):
        return Environment(targets,
                           safemode=self.options.dryrun,
                           movemode=self.options.move,
                           verbosity=self.options.verbosity)

    def logFailure(self, f):
        f.printTraceback()

    def run(self):
        if self.options.script is not None:
            self.runScript(
                ).addErrback(self.logFailure
                ).addCallback(lambda result: reactor.stop())
        else:
            self.runInteractive()

    def runScript(self):
        def _runScript(target):
            env = self.createEnvironment([target])
            return env.runScript(self.options.script)

        return parallel(self.targets, self.MAX_SIMULTANEOUS_SCRIPTS, _runScript)

    def runInteractive(self):
        env = self.createEnvironment(self.targets)
        StandardIO(RenamerInteractive(env))

    def parseOptions(self):
        parser = optparse.OptionParser(usage='%prog [options] input1 [input2 ...]')
        parser.add_option('-t', '--dry-run', dest='dryrun', action='store_true', help='Perform a dry-run')
        parser.add_option('-m', '--move', dest='move', action='store_true', help='Move files')
        parser.add_option('-s', '--script', dest='script', action='store', help='Command script to execute')
        parser.add_option('-v', action='count', dest='verbosity', default=0, help='Increase output verbosity')
        parser.add_option('-g', '--glob', dest='glob', action='store_true', help='Expand filenames as UNIX-style globs')
        parser.add_option('-S', '--sort', dest='sort', action='store', help='Sort filenames by criteria: created, name, size')
        parser.add_option('-R', '--reverse', dest='reverse', action='store_true', help='Reverse filename order')
        options, args = parser.parse_args()

        if options.script and len(args) < 1:
            parser.error('too few arguments')

        if options.glob:
            args = self.expandArgs(args)

        return options, list(args)

    def expandArgs(self, args):
        def _glob():
            return [arg for _arg in args for arg in glob.glob(_arg)]

        def _win32():
            _args = []
            for arg in args:
                if not os.path.exists(arg):
                    globbed = glob.glob(arg)
                    if globbed:
                        _args.extend(globbed)
                        continue

                _args.append(arg)
            return _args

        if sys.platform == 'win32':
            return _win32()

        return _glob()

    def setupLogging(self):
        verbosity = self.options.verbosity
        if verbosity == 0:
            logging.basicConfig(level=logging.WARNING)
        elif verbosity == 1:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.DEBUG)


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

        def log(f):
            f.printTraceback()

        line = line.strip()
        if line:
            self.semaphore.acquire(
                ).addCallback(_doLine
                ).addErrback(log
                ).addBoth(lambda result: self.semaphore.release()
                ).addCallback(lambda result: self.prompt())


def main():
    r = Renamer()
    reactor.callWhenRunning(r.run)
    reactor.run()
